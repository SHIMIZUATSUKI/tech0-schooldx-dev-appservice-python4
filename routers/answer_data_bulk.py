from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import get_db
from models import (
    AnswerDataTable,
    StudentTable,
    LessonTable,
    LessonRegistrationTable,
    QuestionRegistrationTable,
)
from schemas import AnswerDataBulkResponse, BulkInsertResponse

router = APIRouter(prefix="/api/answer-data-bulk", tags=["answer_data_bulk"])


@router.post(
    "/lessons/{lesson_id}/themes/{lesson_theme_id}/generate-answer-data",
    response_model=BulkInsertResponse,
)
async def generate_answer_data_from_theme(
    lesson_id: int,
    lesson_theme_id: int,
    db: Session = Depends(get_db),
):
    """
    授業 lesson_id に対して lesson_theme_id のテーマを持つ
    問題をすべて取得し、クラスの全生徒 × 問題数 分の
    answer_data_table レコードを一括発行します。
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

    # 3. テーマに紐づく問題ID を取得
    qr_list = (
        db.query(QuestionRegistrationTable)
        .filter_by(lesson_theme_id=lesson_theme_id)
        .all()
    )
    if not qr_list:
        raise HTTPException(
            status_code=404,
            detail=f"テーマ {lesson_theme_id} に紐づく問題が見つかりません",
        )
    question_ids = [qr.question_id for qr in qr_list]

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
        db.query(AnswerDataTable)
        .filter(
            AnswerDataTable.lesson_id == lesson_id,
            AnswerDataTable.question_id.in_(question_ids),
        )
        .count()
    )

    # 6. 次の answer_data_id を計算
    max_id = db.execute(
        text("SELECT COALESCE(MAX(answer_data_id), 0) FROM answer_data_table")
    ).scalar()
    next_id = max_id + 1

    # 7. 生徒数 × 問題数 分のレコードを一括生成
    created_records = []
    current_id = next_id
    for student in students:
        for qid in question_ids:
            db.execute(
                text("""
                    INSERT INTO answer_data_table
                      (answer_data_id, student_id, lesson_id, lesson_theme_id, question_id,
                       answer, answer_correctness, answer_status,
                       answer_start_timestamp, answer_start_unix,
                       answer_end_timestamp, answer_end_unix)
                    VALUES
                      (:id, :sid, :lid, :ltid, :qid,
                       NULL, NULL, 0,
                       NULL, NULL,
                       NULL, NULL)
                """),
                {
                    "id": current_id,
                    "sid": student.student_id,
                    "lid": lesson_id,
                    "ltid": lesson_theme_id,
                    "qid": qid,
                },
            )
            created_records.append({
                "answer_data_id": current_id,
                "student_id": student.student_id,
                "lesson_id": lesson_id,
                "lesson_theme_id": lesson_theme_id,
                "question_id": qid,
                "answer": None,
                "answer_correctness": None,
                "answer_status": 0,
                "answer_start_timestamp": None,
                "answer_start_unix": None,
                "answer_end_timestamp": None,
                "answer_end_unix": None,
            })
            current_id += 1

    # 8. コミット
    db.commit()

    # 9. AUTO_INCREMENT を次のIDに合わせる
    db.execute(
        text(f"ALTER TABLE answer_data_table AUTO_INCREMENT = {current_id}")
    )
    db.commit()

    # 10. レスポンス組み立て
    resp_list = [AnswerDataBulkResponse(**r) for r in created_records]
    message = (
        f"授業を開始しました。"
        f"{len(students)}名の生徒に {len(question_ids)}問題ずつ、合計{len(resp_list)}個の回答IDを発行しました。"
        + (f"（既存データ: {existing_count}件）" if existing_count else "")
    )

    return BulkInsertResponse(
        lesson_id=lesson_id,
        lesson_name=lesson.lesson_name or "（無題）",
        total_students=len(students),
        total_questions=len(question_ids),
        total_answer_data=len(resp_list),
        answer_data_list=resp_list,
        message=message,
    )


@router.delete("/answer-data-table/clear")
def clear_answer_data_table(db: Session = Depends(get_db)):
    """
    テスト用 : answer_data_table の全レコードを削除
    """
    try:
        db.execute(text("TRUNCATE TABLE answer_data_table"))
        db.commit()
        return {"message": "answer_data_table の全レコードを削除しました。"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"削除に失敗しました: {e}")

