from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
import models
import schemas

router = APIRouter(prefix="/api/answers", tags=["answers"])

@router.get("/", response_model=List[schemas.AnswerDataWithDetails])
def get_answer_data_for_dashboard(
    lesson_id: int = Query(...),
    db: Session = Depends(get_db)
):
    """
    リアルタイムダッシュボード用API。
    指定された授業の全生徒の回答状況を一括で取得します。
    """
    answer_data_list = db.query(models.LessonAnswerDataTable).options(
        joinedload(models.LessonAnswerDataTable.lesson_question)
    ).filter(models.LessonAnswerDataTable.lesson_id == lesson_id).all()

    if not answer_data_list:
        return []

    response = []
    for ad in answer_data_list:
        if ad.lesson_question:
            response.append(schemas.AnswerDataWithDetails(
                student_id=ad.student_id,
                lesson_id=ad.lesson_id,
                answer_correctness=ad.answer_correctness,
                answer_status=ad.answer_status,
                answer_start_unix=ad.answer_start_unix,
                answer_end_unix=ad.answer_end_unix,
                question=schemas.LessonQuestionResponseForAnswers(
                    lesson_question_id=ad.lesson_question.lesson_question_id,
                    lesson_question_label=ad.lesson_question.lesson_question_label
                )
            ))
    return response