# routers/classes.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import ClassTable
from schemas import ClassResponse

router = APIRouter(prefix="/classes", tags=["classes"])

@router.get("/", response_model=List[ClassResponse])
def get_all_classes(db: Session = Depends(get_db)):
    """
    登録されているクラスの一覧を取得する。
    授業設定画面のクラス選択ドロップダウン用。
    成績表示画面のクラス選択フィルター用。
    """
    classes = db.query(ClassTable).all()
    
    if not classes:
        raise HTTPException(status_code=404, detail="No classes found")
    
    return classes