from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import AnswerDataTable
from schemas import AnswerDataRealtimeResponse

router = APIRouter(
    prefix="/api/answers/realtime_answers_get",
    tags=["answer_data"]
)

@router.get("/", response_model=List[AnswerDataRealtimeResponse])
def get_realtime_answers(
    lesson_theme_id: int = Query(..., description="授業テーマID（必須）"),
    student_id: int = Query(..., description="生徒ID（必須）"),
    question_id: int = Query(..., description="問題ID（必須）"),
    db: Session = Depends(get_db)
):
    answer_data = db.query(AnswerDataTable).filter(
        AnswerDataTable.lesson_theme_id == lesson_theme_id,
        AnswerDataTable.student_id == student_id,
        AnswerDataTable.question_id == question_id
    ).all()

    if not answer_data:
        raise HTTPException(status_code=404, detail="該当する回答データが見つかりません")

    return answer_data