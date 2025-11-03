# ファイルパス: schooldx-ver3-back\routers\classes.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
# ▼▼▼ モデル (StudentTable) と スキーマ (StudentInfo) をインポート ▼▼▼
from models import ClassTable, StudentTable
from schemas import ClassResponse, StudentInfo
# ▲▲▲ インポート追加 ▲▲▲

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

# ▼▼▼▼▼ 【新規追加】 class_id で生徒一覧を取得するAPI ▼▼▼▼▼
@router.get("/{class_id}/students", response_model=List[StudentInfo])
def get_students_by_class(class_id: int, db: Session = Depends(get_db)):
  """
  指定されたクラスIDに所属する生徒の一覧を取得する。
  リアルタイムダッシュボードの生徒一覧表示用。
  (schemas.StudentInfo は student_id, name, class_id を返します)
  """
  students = (
    db.query(StudentTable)
    .filter(StudentTable.class_id == class_id)
    .order_by(StudentTable.students_number) # 出席番号順でソート
    .all()
  )
 
  if not students:
    # 404を返すとフロント側でエラー処理が必要になるため、
    # 空のリストを返す（生徒が0人のクラス）
    return []
 
  return students
# ▲▲▲▲▲ 【新規追加】 ここまで ▲▲▲▲▲