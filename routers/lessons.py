from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import (
    LessonTable, 
    LessonAnswerDataTable, 
    LessonRegistrationTable,
    StudentTable,
    LessonQuestionsTable,
    LessonThemesTable,
    LessonThemeContentsTable
)
from pydantic import BaseModel

router = APIRouter(prefix="/api/lessons", tags=["lessons"])

class LessonStatusResponse(BaseModel):
    message: str

@router.put("/{lesson_id}/start", response_model=LessonStatusResponse)
async def start_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
):
    """
    ② 授業開始処理
    - lesson_statusを2(進行中)に更新
    - 全生徒分の回答データを生成
    """
    # 授業の存在確認
    lesson = db.query(LessonTable).filter_by(lesson_id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # ステータスを進行中(2)に更新
    lesson.lesson_status = 2
    
    # この授業に紐づく全テーマIDを取得
    lesson_theme_ids = (
        db.query(LessonRegistrationTable.lesson_theme_id)
        .filter(LessonRegistrationTable.lesson_id == lesson_id)
        .all()
    )
    
    # クラスの全生徒を取得
    students = (
        db.query(StudentTable)
        .filter_by(class_id=lesson.class_id)
        .all()
    )
    
    if not students:
        raise HTTPException(
            status_code=404, 
            detail="No students found in this class"
        )
    
    created_count = 0
    
    # 各テーマごとに処理
    for (theme_id,) in lesson_theme_ids:
        # テーマに紐づく問題を取得（4問想定）
        questions = (
            db.query(LessonQuestionsTable)
            .join(LessonThemeContentsTable)
            .join(LessonThemesTable)
            .filter(LessonThemesTable.lesson_theme_id == theme_id)
            .limit(4)  # 1テーマあたり4問
            .all()
        )
        
        # 既存データの確認
        existing_count = (
            db.query(LessonAnswerDataTable)
            .filter(
                LessonAnswerDataTable.lesson_id == lesson_id,
                LessonAnswerDataTable.lesson_theme_id == theme_id,
            )
            .count()
        )
        
        # 既にデータがある場合はスキップ
        if existing_count > 0:
            continue
        
        # 生徒数 × 問題数のレコードを作成
        for student in students:
            for question in questions:
                new_data = LessonAnswerDataTable(
                    student_id=student.student_id,
                    lesson_id=lesson_id,
                    lesson_theme_id=theme_id,
                    lesson_question_id=question.lesson_question_id,
                    choice_number=None,
                    answer_correctness=None,
                    answer_status=1,  # READY
                    answer_start_timestamp=None,
                    answer_start_unix=None,
                    answer_end_timestamp=None,
                    answer_end_unix=None
                )
                db.add(new_data)
                created_count += 1
    
    db.commit()
    
    return LessonStatusResponse(
        message=f"Lesson started successfully. Created {created_count} answer records."
    )

@router.put("/{lesson_id}/end", response_model=LessonStatusResponse)
async def end_lesson(
    lesson_id: int,
    db: Session = Depends(get_db),
):
    """
    ⑦ 授業終了処理
    - lesson_statusを3(終了)に更新
    """
    # 授業の存在確認
    lesson = db.query(LessonTable).filter_by(lesson_id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # ステータスを終了(3)に更新
    lesson.lesson_status = 3
    db.commit()
    
    return LessonStatusResponse(message="Lesson ended successfully")