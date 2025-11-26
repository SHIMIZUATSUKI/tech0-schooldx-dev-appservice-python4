from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import LessonThemeContentsTable, LessonThemesTable, LessonRegistrationTable
from pydantic import BaseModel

router = APIRouter(prefix="/api/lesson_themes", tags=["lesson_themes"])

class ExerciseStatusResponse(BaseModel):
    message: str

@router.put("/{lesson_theme_id}/start_exercise", response_model=ExerciseStatusResponse)
async def start_exercise(
    lesson_theme_id: int,
    db: Session = Depends(get_db),
):
    """
    ④ 演習開始処理
    - lesson_question_statusを2(進行中)に更新
    """
    # テーマに紐づくlesson_theme_contentsを取得
    # content = (
    #     db.query(LessonThemeContentsTable)
    #     .join(LessonThemesTable)
    #     .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
    #     .first()
    # )
    content = (
        db.query(LessonRegistrationTable)
        .join(LessonThemesTable)
        .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
        .first()
    )
    if not content:
        raise HTTPException(
            status_code=404, 
            detail=f"Theme content not found for lesson_theme_id: {lesson_theme_id}"
        )
    
    # ステータスを進行中(2)に更新
    content.lesson_question_status = 2
    db.commit()
    
    return ExerciseStatusResponse(message="Exercise started")

@router.put("/{lesson_theme_id}/end_exercise", response_model=ExerciseStatusResponse)
async def end_exercise(
    lesson_theme_id: int,
    db: Session = Depends(get_db),
):
    """
    ⑤ 演習終了処理
    - lesson_question_statusを3(終了)に更新
    """
    # テーマに紐づくlesson_theme_contentsを取得
    # content = (
    #     db.query(LessonThemeContentsTable)
    #     .join(LessonThemesTable)
    #     .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
    #     .first()
    # )
    content = (
        db.query(LessonRegistrationTable)
        .join(LessonThemesTable)
        .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
        .first()
    )    
    if not content:
        raise HTTPException(
            status_code=404, 
            detail=f"Theme content not found for lesson_theme_id: {lesson_theme_id}"
        )
    
    # ステータスを終了(3)に更新
    content.lesson_question_status = 3
    db.commit()
    
    return ExerciseStatusResponse(message="Exercise ended")