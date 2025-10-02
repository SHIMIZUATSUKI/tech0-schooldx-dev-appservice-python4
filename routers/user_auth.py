from __future__ import annotations

from sqlalchemy.orm import Session
from database import get_db
from models import StudentTable

from fastapi import APIRouter, Depends,HTTPException, status
from pydantic import BaseModel, EmailStr

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/")
def read_test():
    return {"status": "ok"}




# ======================
# リクエストスキーマ
# ======================
class LoginRequest(BaseModel):
    email: EmailStr
    # idToken: str   # 今回は未使用

@router.post("/login", status_code=status.HTTP_200_OK)
def allow_login(
        req: LoginRequest,
        db: Session = Depends(get_db)
    ):
    
    # 1. studentの存在確認 (メールアドレスで確認)
    student = db.query(StudentTable).filter_by(mail_address = req.email).first()

    if not student:
        raise HTTPException(status_code=404, detail="登録されていない生徒です")

    return {
        "status": "ok",
        "user_id": student.student_id,
        # "email": student.email,
        "class_id": student.class_id,
        # "class_name": student.class_name
    }