# ファイルパス: routers\lessons.py
# 【最適化版】start_lesson 関数

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
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
    ② 授業開始処理 (パフォーマンス最適化版)
    - lesson_statusを2(進行中)に更新
    - 全生徒分の回答データを一括生成
    
    【最適化ポイント】
    1. テーマIDと問題IDを事前に一括取得 (N+1問題解消)
    2. 既存データチェックを1回のクエリで実行
    3. bulk_insert_mappings で高速一括INSERT
    """
    
    # ========================================
    # 1. 授業の存在確認 (クエリ x 1)
    # ========================================
    lesson = db.query(LessonTable).filter_by(lesson_id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # ステータスを進行中(2)に更新
    lesson.lesson_status = 2

    # ========================================
    # 2. この授業に紐づく全テーマIDを取得 (クエリ x 1)
    # ========================================
    theme_id_tuples = (
        db.query(LessonRegistrationTable.lesson_theme_id)
        .filter(LessonRegistrationTable.lesson_id == lesson_id)
        .all()
    )
    if not theme_id_tuples:
        # 授業にテーマが登録されていない場合はステータス更新だけコミットして終了
        db.commit()
        return LessonStatusResponse(
            message=f"Lesson started successfully. No themes registered, 0 records created."
        )
    
    lesson_theme_ids = [theme_id for (theme_id,) in theme_id_tuples]

    # ========================================
    # 3. 【最適化】既存データを一括チェック (クエリ x 1)
    # ========================================
    existing_data_counts = (
        db.query(
            LessonAnswerDataTable.lesson_theme_id,
            func.count(LessonAnswerDataTable.lesson_answer_data_id).label("count")
        )
        .filter(
            LessonAnswerDataTable.lesson_id == lesson_id,
            LessonAnswerDataTable.lesson_theme_id.in_(lesson_theme_ids)
        )
        .group_by(LessonAnswerDataTable.lesson_theme_id)
        .all()
    )
    
    # 既にデータが存在するテーマIDのセット
    existing_theme_ids = {theme_id for theme_id, count in existing_data_counts if count > 0}

    # ========================================
    # 4. クラスの全生徒を取得 (クエリ x 1)
    # ========================================
    students = (
        db.query(StudentTable)
        .filter_by(class_id=lesson.class_id)
        .all()
    )
    
    if not students:
        db.commit() # ステータス更新を反映
        raise HTTPException(
            status_code=404,
            detail="No students found in this class"
        )

    # ========================================
    # 5. これから登録すべきテーマID (既存のものを除く)
    # ========================================
    themes_to_create_ids = [theme_id for theme_id in lesson_theme_ids if theme_id not in existing_theme_ids]

    if not themes_to_create_ids:
        db.commit() # ステータス更新を反映
        # 既に全データが作成済みの場合
        existing_total_count = sum(count for _, count in existing_data_counts)
        return LessonStatusResponse(
            message=f"Lesson started successfully. All {existing_total_count} answer records already exist."
        )

    # ========================================
    # 6. 【最適化】全テーマの問題IDを一括取得 (クエリ x 1)
    # ========================================
    # テーマIDごとに問題IDを取得し、辞書に格納
    theme_questions_query = (
        db.query(
            LessonThemesTable.lesson_theme_id,
            LessonQuestionsTable.lesson_question_id
        )
        .join(LessonThemeContentsTable, LessonThemesTable.lesson_theme_contents_id == LessonThemeContentsTable.lesson_theme_contents_id)
        .join(LessonQuestionsTable, LessonThemeContentsTable.lesson_theme_contents_id == LessonQuestionsTable.lesson_theme_contents_id)
        .filter(LessonThemesTable.lesson_theme_id.in_(themes_to_create_ids))
        .order_by(LessonThemesTable.lesson_theme_id, LessonQuestionsTable.lesson_question_id.asc())
        .all()
    )

    # テーマIDをキーとした問題IDリストの辞書を作成
    theme_to_questions = {}
    for theme_id, question_id in theme_questions_query:
        if theme_id not in theme_to_questions:
            theme_to_questions[theme_id] = []
        # 最大4問まで
        if len(theme_to_questions[theme_id]) < 4:
            theme_to_questions[theme_id].append(question_id)

    # ========================================
    # 7. 【最適化】INSERT用データを一括作成
    # ========================================
    new_records_to_add = []
    
    for theme_id in themes_to_create_ids:
        question_ids = theme_to_questions.get(theme_id, [])
        
        if not question_ids:
            continue  # 問題がない場合はスキップ
        
        # 生徒ごと、問題ごとにレコードを作成
        for student in students:
            for question_id in question_ids:
                new_records_to_add.append({
                    'student_id': student.student_id,
                    'lesson_id': lesson_id,
                    'lesson_theme_id': theme_id,
                    'lesson_question_id': question_id,
                    'choice_number': None,
                    'answer_correctness': None,
                    'answer_status': 1,  # READY
                    'answer_start_timestamp': None,
                    'answer_start_unix': None,
                    'answer_end_timestamp': None,
                    'answer_end_unix': None
                })
    
    created_count = len(new_records_to_add)

    # ========================================
    # 8. 【最適化】bulk_insert_mappings で高速一括INSERT
    # ========================================
    if new_records_to_add:
        db.bulk_insert_mappings(LessonAnswerDataTable, new_records_to_add)

    # ========================================
    # 9. コミット (COMMIT x 1)
    # ========================================
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
    ⑥ 授業終了処理
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