from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from database import get_db
from models import LessonAnswerDataTable
from schemas import AnswerUpdateRequest, AnswerData
from datetime import datetime

router = APIRouter(prefix="/api/answers", tags=["answer_data"])

@router.put("/", response_model=AnswerData)
def update_answer_data_by_id(
    lesson_answer_data_id: int = Query(..., description="更新対象の answer_data_id"),
    update: AnswerUpdateRequest = Body(...),
    db: Session = Depends(get_db)
):
    # レコード取得
    record = db.query(LessonAnswerDataTable).filter(
        LessonAnswerDataTable.lesson_answer_data_id == lesson_answer_data_id
    ).first()

    if not record:
        raise HTTPException(status_code=404, detail="Answer data not found.")

    # nullの場合は更新スキップ（かつUNIX時刻自動算出対応）
    if update.answer_correctness is not None:
        record.answer_correctness = update.answer_correctness

    if update.answer_status is not None:
        record.answer_status = update.answer_status

    if update.answer_start_timestamp is not None:
        record.answer_start_timestamp = update.answer_start_timestamp
        record.answer_start_unix = int(update.answer_start_timestamp.timestamp())

    elif update.answer_start_unix is not None:
        record.answer_start_unix = update.answer_start_unix

    if update.answer_end_timestamp is not None:
        record.answer_end_timestamp = update.answer_end_timestamp
        record.answer_end_unix = int(update.answer_end_timestamp.timestamp())

    elif update.answer_end_unix is not None:
        record.answer_end_unix = update.answer_end_unix

    # DB反映
    db.commit()
    db.refresh(record)

    return AnswerData(
        answer_data_id=record.lesson_answer_data_id,
        student_id=record.student_id,
        lesson_id=record.lesson_id or 0,
        lesson_theme_id=record.lesson_theme_id or 0,
        question_id=record.lesson_question_id,
        choice_number=record.choice_number or 0,
        answer_correctness=int(record.answer_correctness) if record.answer_correctness is not None else 0,
        answer_status=record.answer_status or 0,
        answer_start_timestamp=record.answer_start_timestamp or datetime.now(),
        answer_start_unix=record.answer_start_unix or 0,
        answer_end_timestamp=record.answer_end_timestamp or datetime.now(),
        answer_end_unix=record.answer_end_unix or 0
    )
    