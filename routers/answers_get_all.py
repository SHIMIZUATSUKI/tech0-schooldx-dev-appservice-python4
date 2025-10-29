from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import LessonAnswerDataTable, LessonQuestionsTable, StudentTable, LessonTable
from schemas import LessonAnswerDataWithDetails, LessonQuestionResponse
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/answers", tags=["answer_data"])

@router.get("/", response_model=List[LessonAnswerDataWithDetails])
def get_answer_data_with_details(
    student_id: Optional[int] = Query(None, description="生徒ID（オプション）"),
    lesson_id: Optional[int] = Query(None, description="授業ID（オプション）"),
    db: Session = Depends(get_db)
):
    """
    リアルタイムダッシュボード用。
    lesson_idで授業全体の全生徒データを一括取得（パフォーマンス改善）。
    student_idも指定された場合は、その生徒のみのデータを返す。
    """
    query = db.query(LessonAnswerDataTable).options(
        joinedload(LessonAnswerDataTable.lesson_question)
    )
    
    # フィルター条件
    if lesson_id:
        query = query.filter(LessonAnswerDataTable.lesson_id == lesson_id)
    if student_id:
        query = query.filter(LessonAnswerDataTable.student_id == student_id)
    
    # いずれも指定されていない場合はエラー
    if not lesson_id and not student_id:
        raise HTTPException(status_code=400, detail="lesson_id or student_id must be provided")
    
    records = query.all()
    
    if not records:
        return []
    
    result = []
    for row in records:
        question = row.lesson_question

        if not question:
                continue

        # 問題詳細の構築
        question_detail = LessonQuestionResponse(
            lesson_question_id=question.lesson_question_id,
            lesson_question_label=question.lesson_question_label or f"問{question.lesson_question_id}",
            question_text1=question.question_text1,
            question_text2=question.question_text2,
            question_text3=question.question_text3,
            question_text4=question.question_text4,
            correctness_number=question.correctness_number
        )
        
        result.append(LessonAnswerDataWithDetails(
            lesson_answer_data_id=row.lesson_answer_data_id,
            student_id=row.student_id,
            lesson_id=row.lesson_id,
            lesson_theme_id=row.lesson_theme_id,
            answer_correctness=int(row.answer_correctness) if row.answer_correctness is not None else None,
            answer_status=row.answer_status,
            answer_start_timestamp=row.answer_start_timestamp,
            answer_start_unix=row.answer_start_unix,
            answer_end_timestamp=row.answer_end_timestamp,
            answer_end_unix=row.answer_end_unix,
            question=question_detail
        ))
    
    return result