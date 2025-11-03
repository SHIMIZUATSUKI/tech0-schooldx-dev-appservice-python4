# ファイルパス: schooldx-ver3-back/routers/students.py
# (新規作成)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import StudentTable, ClassTable
from pydantic import BaseModel

router = APIRouter(prefix="/api/students", tags=["students"])

class StudentResponse(BaseModel):
  student_id: int
  class_id: int
  students_number: int
  name: str
 
  class Config:
    from_attributes = True

@router.get("/by-class/{class_id}", response_model=List[StudentResponse])
def get_students_by_class(class_id: int, db: Session = Depends(get_db)):
  """
  指定されたクラスIDに所属する生徒の一覧を取得する。
  リアルタイムダッシュボードの初期表示用。
  """
  class_exists = db.query(ClassTable).filter(ClassTable.class_id == class_id).first()
  if not class_exists:
    raise HTTPException(status_code=404, detail="指定されたクラスが見つかりません")
 
  students = (
    db.query(StudentTable)
    .filter(StudentTable.class_id == class_id)
    .order_by(StudentTable.students_number) # 出席番号順にソート
    .all()
  )
 
  if not students:
    # クラスは存在するが、生徒がいない場合は空リストを返す
    return []
 
  return students