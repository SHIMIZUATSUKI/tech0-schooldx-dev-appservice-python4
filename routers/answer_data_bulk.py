from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import (
    LessonAnswerDataTable,
    StudentTable,
    LessonTable,
    LessonRegistrationTable,
    LessonQuestionsTable,
    LessonThemesTable,
    LessonThemeContentsTable
)

router = APIRouter(prefix="/api/answer-data-bulk", tags=["answer_data_bulk"])

@router.post("/lessons/{lesson_id}/themes/{lesson_theme_id}/generate-answer-data")
async def generate_answer_data(
    lesson_id: int,
    lesson_theme_id: int,
    db: Session = Depends(get_db),
):
    """
    授業開始時に生徒全員分の回答データを一括生成
    lesson_answer_data_table用に変更
    """
    # 1. 授業の存在確認
    lesson = db.query(LessonTable).filter_by(lesson_id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="授業が見つかりません")
    
    # 2. その授業にテーマが登録されているか確認
    registration = (
        db.query(LessonRegistrationTable)
        .filter_by(lesson_id=lesson_id, lesson_theme_id=lesson_theme_id)
        .first()
    )
    if not registration:
        raise HTTPException(
            status_code=404,
            detail=f"授業 {lesson_id} にテーマ {lesson_theme_id} は登録されていません",
        )
    
    # 3. テーマに紐づく問題を取得
    # lesson_theme_contents_tableを経由してlesson_questions_tableから取得
    questions = (
        db.query(LessonQuestionsTable)
        .join(LessonThemeContentsTable)
        .join(LessonThemesTable)
        .filter(LessonThemesTable.lesson_theme_id == lesson_theme_id)
        .all()
    )
    
    if not questions:
        raise HTTPException(
            status_code=404,
            detail=f"テーマ {lesson_theme_id} に紐づく問題が見つかりません",
        )
    
    # 4. クラスの生徒を取得
    students = (
        db.query(StudentTable)
        .filter_by(class_id=lesson.class_id)
        .all()
    )
    if not students:
        raise HTTPException(
            status_code=404,
            detail="該当クラスに生徒が登録されていません",
        )
    
    # 5. 既存データ数の確認
    existing_count = (
        db.query(LessonAnswerDataTable)
        .filter(
            LessonAnswerDataTable.lesson_id == lesson_id,
            LessonAnswerDataTable.lesson_theme_id == lesson_theme_id,
        )
        .count()
    )
    
    if existing_count > 0:
        return {
            "message": f"既にデータが作成済みです（{existing_count}件）",
            "lesson_id": lesson_id,
            "lesson_theme_id": lesson_theme_id,
            "total_existing": existing_count
        }
    
    # 6. 生徒数 × 問題数 分のレコードを一括生成
    created_count = 0
    for student in students:
        for question in questions:
            new_data = LessonAnswerDataTable(
                student_id=student.student_id,
                lesson_id=lesson_id,
                lesson_theme_id=lesson_theme_id,
                lesson_question_id=question.lesson_question_id,
                choice_number=None,
                answer_correctness=None,
                answer_status=1,  # READY (初期状態)
                answer_start_timestamp=None,
                answer_start_unix=None,
                answer_end_timestamp=None,
                answer_end_unix=None
            )
            db.add(new_data)
            created_count += 1
    
    # 7. コミット
    db.commit()
    
    # 8. レスポンス組み立て
    message = (
        f"授業を開始しました。"
        f"{len(students)}名の生徒に {len(questions)}問題ずつ、合計{created_count}個の回答データを作成しました。"
    )
    
    return {
        "message": message,
        "lesson_id": lesson_id,
        "lesson_theme_id": lesson_theme_id,
        "total_students": len(students),
        "total_questions": len(questions),
        "total_created": created_count
    }