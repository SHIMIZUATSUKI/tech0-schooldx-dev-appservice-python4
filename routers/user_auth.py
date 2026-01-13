from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from sqlalchemy.orm import Session
from database import get_db
from models import StudentTable, LoginHistoryTable 

router = APIRouter(prefix="/auth", tags=["auth"])

# Authorization: Bearer <token> を受け取る
security = HTTPBearer(auto_error=False)


# ======================
# Firebase Admin 初期化
# ======================

def init_firebase_admin() -> None:
    """
    Firebase Admin SDK を1回だけ初期化する。
    優先順位：
      1) 環境変数 FIREBASE_SERVICE_ACCOUNT_JSON（JSON本文）
      2) 環境変数 GOOGLE_APPLICATION_CREDENTIALS or FIREBASE_SERVICE_ACCOUNT_PATH（ファイルパス）
      3) カレントディレクトリの serviceAccountKey.json（ローカル開発用）
    """
    if firebase_admin._apps:
        return

    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if sa_json:
        try:
            sa_dict = json.loads(sa_json)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"FIREBASE_SERVICE_ACCOUNT_JSON is not valid JSON: {e}")

        cred = credentials.Certificate(sa_dict)
        firebase_admin.initialize_app(cred)
        return

    sa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
    if sa_path and os.path.exists(sa_path):
        firebase_admin.initialize_app(credentials.Certificate(sa_path))
        return

    # ローカル用フォールバック（必要ならパスは適宜変更）
    local_path = os.path.join(os.getcwd(), "serviceAccountKey.json")
    if os.path.exists(local_path):
        firebase_admin.initialize_app(credentials.Certificate(local_path))
        return

    raise RuntimeError(
        "Firebase Admin credential not found. "
        "Set FIREBASE_SERVICE_ACCOUNT_JSON (recommended) or GOOGLE_APPLICATION_CREDENTIALS/FIREBASE_SERVICE_ACCOUNT_PATH, "
        "or place serviceAccountKey.json for local dev."
    )

def _insert_login_history(
    db: Session,
    *,
    email: Optional[str],
    firebase_uid: Optional[str],
    student_id: Optional[int],
    token_valid: bool,
    is_whitelisted: bool,
    result: str,
    reason_code: Optional[str],
    http_status: Optional[int],
) -> None:
    row = LoginHistoryTable(
        mail_address=email,
        firebase_uid=firebase_uid,
        student_id=student_id,
        token_valid=1 if token_valid else 0,
        is_whitelisted=1 if is_whitelisted else 0,
        result=result,
        reason_code=reason_code,
        http_status=http_status,
    )
    db.add(row)
    db.commit()


def verify_bearer_token(id_token: str) -> Dict[str, Any]:
    """
    IDトークンを検証してデコード結果を返す。
    失敗したら例外を投げる。
    """
    init_firebase_admin()
    return auth.verify_id_token(id_token)


def get_decoded_token(
    creds: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    try:
        return verify_bearer_token(creds.credentials)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}")


# ======================
# ルーティング
# ======================

@router.get("/")
def read_test():
    return {"status": "ok"}

@router.post("/login", status_code=status.HTTP_200_OK)
def login(
    db: Session = Depends(get_db),
    creds: HTTPAuthorizationCredentials = Depends(security),
):
    """
    - Bearer IDトークン検証
    - DBホワイトリスト照合
    - 成否に関わらず login_history に記録
    """
    init_firebase_admin()

    # 1) Bearerチェック
    if creds is None or creds.scheme.lower() != "bearer":
        _insert_login_history(
            db,
            email=None,
            firebase_uid=None,
            student_id=None,
            token_valid=False,
            is_whitelisted=False,
            result="REJECTED",
            reason_code="MISSING_TOKEN",
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    id_token = creds.credentials

    # 2) トークン検証
    try:
        decoded: Dict[str, Any] = auth.verify_id_token(id_token)
    except Exception:
        _insert_login_history(
            db,
            email=None,
            firebase_uid=None,
            student_id=None,
            token_valid=False,
            is_whitelisted=False,
            result="REJECTED",
            reason_code="INVALID_TOKEN",
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    uid = decoded.get("uid")
    email = decoded.get("email")

    if not uid:
        _insert_login_history(
            db,
            email=email,
            firebase_uid=None,
            student_id=None,
            token_valid=True,
            is_whitelisted=False,
            result="REJECTED",
            reason_code="UID_MISSING",
            http_status=status.HTTP_401_UNAUTHORIZED,
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="uid missing in token")

    if not email:
        _insert_login_history(
            db,
            email=None,
            firebase_uid=uid,
            student_id=None,
            token_valid=True,
            is_whitelisted=False,
            result="REJECTED",
            reason_code="EMAIL_MISSING",
            http_status=status.HTTP_403_FORBIDDEN,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="email missing in token")

    # 3) ホワイトリスト照合（DB）
    student = db.query(StudentTable).filter_by(mail_address=email).first()

    if not student:
        _insert_login_history(
            db,
            email=email,
            firebase_uid=uid,
            student_id=None,
            token_valid=True,
            is_whitelisted=False,
            result="REJECTED",
            reason_code="NOT_REGISTERED",
            http_status=status.HTTP_403_FORBIDDEN,
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not allowed (not whitelisted)")

    # 4) 在籍フラグ等があるならここで弾く
    # if hasattr(student, "is_active") and not student.is_active:
    #         ... reason_code="INACTIVE" ...

    # 5) 成功
    _insert_login_history(
        db,
        email=email,
        firebase_uid=uid,
        student_id=getattr(student, "student_id", None),
        token_valid=True,
        is_whitelisted=True,
        result="SUCCESS",
        reason_code=None,
        http_status=status.HTTP_200_OK,
    )

    return {
        "status": "ok",
        "user_id": student.student_id,
        "class_id": student.class_id,
        "class_name": student.class_ref.class_name
    }