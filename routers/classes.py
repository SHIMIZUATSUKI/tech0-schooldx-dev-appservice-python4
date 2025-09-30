# routers/classes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from models import ClassTable
from schemas import ClassResponse

# ▼▼▼ 末尾スラッシュを追加 ▼▼▼
router = APIRouter(prefix="/classes", tags=["classes"])

@router.get("/")  # これは /classes/ にマッチする
# ▲▲▲ 修正ここまで ▲▲▲
def get_all_classes(db: Session = Depends(get_db)):
    """
    登録されているクラスの一覧を取得する。
    """
    classes = db.query(ClassTable).all()
    
    if not classes:
        raise HTTPException(status_code=404, detail="No classes found")
    
    return classes