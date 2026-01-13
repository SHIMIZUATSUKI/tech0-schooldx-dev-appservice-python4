from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import LessonTable, LessonThemesTable, LessonRegistrationTable
from pydantic import BaseModel

router = APIRouter(prefix="/api/lesson_themes", tags=["lesson_themes"])

class ExerciseStatusResponse(BaseModel):
    message: str

@router.put("/{lesson_id}/{lesson_theme_id}/start_exercise", response_model=ExerciseStatusResponse)
async def start_exercise(
    lesson_id: int,
    lesson_theme_id: int,
    db: Session = Depends(get_db),
):
    """
    ④ 演習開始処理
    - lesson_question_statusを2(進行中)に更新
    """
    # 講義IDとテーマIDで絞ってstatusを取得
    content = (
        db.query(LessonRegistrationTable)
        .join(LessonTable)
        .join(LessonThemesTable)
        .filter(LessonTable.lesson_id == lesson_id)
        .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
        .first()
    )
    if not content:
        raise HTTPException(
            status_code=404, 
            detail=f"No registration record found for lesson_id={lesson_id} and lesson_theme_id={lesson_theme_id}."
        )
    
    # ステータスを進行中(2)に更新
    content.lesson_question_status = 2
    db.commit()
    
    return ExerciseStatusResponse(message="Exercise started")

@router.put("/{lesson_id}/{lesson_theme_id}/end_exercise", response_model=ExerciseStatusResponse)
async def end_exercise(
    lesson_id: int,
    lesson_theme_id: int,
    db: Session = Depends(get_db),
):
    """
    ⑤ 演習終了処理
    - lesson_question_statusを3(終了)に更新
    """
    # 講義IDとテーマIDで絞ってstatusを取得
    content = (
        db.query(LessonRegistrationTable)
        .join(LessonTable)
        .join(LessonThemesTable)
        .filter(LessonTable.lesson_id == lesson_id)        
        .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
        .first()
    )    
    if not content:
        raise HTTPException(
            status_code=404, 
            detail=f"No registration record found for lesson_id={lesson_id} and lesson_theme_id={lesson_theme_id}."
        )
    
    # ステータスを終了(3)に更新
    content.lesson_question_status = 3
    db.commit()
    
    return ExerciseStatusResponse(message="Exercise ended")


class QuestionCountResponse(BaseModel):
    lesson_theme_id: int
    question_count: int
    question_ids: list[int]


@router.get("/{lesson_theme_id}/questions/count", response_model=QuestionCountResponse)
async def get_question_count(
    lesson_theme_id: int,
    db: Session = Depends(get_db),
):
    """
    テーマに紐づく問題数を取得
    """
    from models import LessonQuestionsTable, LessonThemeContentsTable
    
    # テーマに紐づく問題を取得
    questions = (
        db.query(LessonQuestionsTable)
        .join(LessonThemeContentsTable)
        .join(LessonThemesTable)
        .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
        .order_by(LessonQuestionsTable.lesson_question_id)
        .all()
    )
    
    question_ids = [q.lesson_question_id for q in questions]
    
    return QuestionCountResponse(
        lesson_theme_id=lesson_theme_id,
        question_count=len(questions),
        question_ids=question_ids
    )