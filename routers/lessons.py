from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, row_number  # ◀ 必要なモジュールを追加
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
    ② 授業開始処理 (パフォーマンス改善版)
    - lesson_statusを2(進行中)に更新
    - 全生徒分の回答データを一括生成
    """
    
    # 1. 授業の存在確認 (クエリ x 1)
    lesson = db.query(LessonTable).filter_by(lesson_id=lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # 2. ステータスを進行中(2)に更新
    # (コミットは最後に行う)
    lesson.lesson_status = 2
    
    # 3. この授業に紐づく全テーマIDを取得 (クエリ x 1)
    theme_id_tuples = (
        db.query(LessonRegistrationTable.lesson_theme_id)
        .filter(LessonRegistrationTable.lesson_id == lesson_id)
        .all()
    )
    
    if not theme_id_tuples:
        # 授業にテーマが登録されていない場合は、ステータス更新だけコミットして終了
        db.commit()
        return LessonStatusResponse(
            message=f"Lesson started successfully. No themes registered, 0 records created."
        )
        
    lesson_theme_ids = [theme_id for (theme_id,) in theme_id_tuples]

    # 4. [改善] 既存データを「テーマIDごと」に一括で取得 (クエリ x 1)
    # (N+1クエリ解消)
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

    # 5. クラスの全生徒を取得 (クエリ x 1)
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

    # 6. [改善] これから登録すべきテーマID (既存のものを除く)
    themes_to_create_ids = [theme_id for theme_id in lesson_theme_ids if theme_id not in existing_theme_ids]

    if not themes_to_create_ids:
        db.commit() # ステータス更新を反映
        return LessonStatusResponse(
            message=f"Lesson started successfully. All answer records already exist."
        )

    # 7. [改善] 対象テーマの問題を「1テーマ4問まで」で一括取得 (クエリ x 1)
    # (N+1クエリ解消 + limit(4)のバグ修正)
    
    # サブクエリで各テーマ内の問題に番号を振る
    # (LessonQuestionsTable.lesson_question_id の昇順で4件取得)
    subquery = (
        db.query(
            LessonQuestionsTable.lesson_question_id,
            LessonThemesTable.lesson_theme_id,
            func.row_number().over(
                partition_by=LessonThemesTable.lesson_theme_id,
                order_by=LessonQuestionsTable.lesson_question_id.asc()
            ).label("rn")
        )
        .join(LessonThemeContentsTable, LessonQuestionsTable.lesson_theme_contents_id == LessonThemeContentsTable.lesson_theme_contents_id)
        .join(LessonThemesTable, LessonThemeContentsTable.lesson_theme_contents_id == LessonThemesTable.lesson_theme_contents_id)
        .filter(LessonThemesTable.lesson_theme_id.in_(themes_to_create_ids))
        .subquery()
    )
    
    # 番号が4以下の問題IDとテーマIDを取得
    questions_query = (
        db.query(
            subquery.c.lesson_theme_id,
            subquery.c.lesson_question_id
        )
        .filter(subquery.c.rn <= 4)
        .all()
    )
    
    # Python側で {theme_id: [question_id, ...]} のマップを作成
    theme_to_questions_map = {}
    for theme_id, question_id in questions_query:
        if theme_id not in theme_to_questions_map:
            theme_to_questions_map[theme_id] = []
        theme_to_questions_map[theme_id].append(question_id)

    # 8. [改善] 一括INSERT用のリストを作成
    new_records_to_add = []
    
    # Pythonループ (DBアクセスなし)
    for student in students:
        for theme_id in themes_to_create_ids:
            questions_ids = theme_to_questions_map.get(theme_id, [])
            for question_id in questions_ids:
                new_data = LessonAnswerDataTable(
                    student_id=student.student_id,
                    lesson_id=lesson_id,
                    lesson_theme_id=theme_id,
                    lesson_question_id=question_id,
                    choice_number=None,
                    answer_correctness=None,
                    answer_status=1,  # READY
                    answer_start_timestamp=None,
                    answer_start_unix=None,
                    answer_end_timestamp=None,
                    answer_end_unix=None
                )
                new_records_to_add.append(new_data)
    
    created_count = len(new_records_to_add)

    # 9. [改善] 一括INSERT (Bulk Insert)
    if new_records_to_add:
        db.add_all(new_records_to_add)
    
    # 10. コミット (COMMIT x 1)
    # (ステータス更新とINSERTが一括でコミットされる)
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