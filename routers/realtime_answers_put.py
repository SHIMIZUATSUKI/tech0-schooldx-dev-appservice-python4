from fastapi import APIRouter, Depends, HTTPException, Query, Body, BackgroundTasks # ★ 1. BackgroundTasks をインポート
from sqlalchemy.orm import Session
from database import get_db
from models import LessonAnswerDataTable
from schemas import LessonAnswerDataResponse,LessonAnswerUpdateRequest
from datetime import datetime
from socket_server import emit_to_web # ★ 2. emit_to_web ヘルパーをインポート


from fastapi import Request, Response
import time
import uuid

router = APIRouter(prefix="/api/answers", tags=["answer_data"])

@router.put("/", response_model=LessonAnswerDataResponse)
async def update_answer_data_by_id(
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    lesson_answer_data_id: int = Query(..., description="更新対象の answer_data_id"),
    update: LessonAnswerUpdateRequest = Body(...),
    db: Session = Depends(get_db),
):
    # 相関ID（Flutter から来たものがあればそれを採用）
    req_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())

    # 計測用
    t0 = time.perf_counter()
    t = t0
    timings = {}

    def mark(name: str):
        nonlocal t
        now = time.perf_counter()
        timings[name] = (now - t) * 1000  # ms
        t = now

    try:
        # 1) レコード取得（SELECT）
        record = (
            db.query(LessonAnswerDataTable)
            .filter(LessonAnswerDataTable.lesson_answer_data_id == lesson_answer_data_id)
            .first()
        )
        mark("db_select")

        if not record:
            raise HTTPException(status_code=404, detail="Answer data not found.")

        # 2) 値セット（Python側ローカル処理）
        if update.choice_number is not None:
            record.choice_number = update.choice_number

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

        mark("apply_update")

        # 3) DB反映（UPDATE/COMMIT）
        db.commit()
        mark("db_commit")

        # 4) refresh（SELECTが走ることがあります）
        db.refresh(record)
        mark("db_refresh")

        # 5) Socket.IO enqueue（※ add_task は通常ほぼ0ms。実処理はレスポンス後）
        if record.lesson_id:
            emit_data = f"student_answered,{record.lesson_id},{record.student_id},{record.lesson_answer_data_id}"
            background_tasks.add_task(emit_to_web, 'from_flutter', emit_data)
        mark("bg_enqueue")

        # 6) レスポンス生成（Pydantic等）
        res = LessonAnswerDataResponse(
            lesson_answer_data_id=record.lesson_answer_data_id,
            student_id=record.student_id,
            lesson_id=record.lesson_id or 0,
            lesson_theme_id=record.lesson_theme_id or 0,
            lesson_question_id=record.lesson_question_id,
            choice_number=record.choice_number or 0,
            answer_correctness=int(record.answer_correctness) if record.answer_correctness is not None else 0,
            answer_status=record.answer_status or 0,
            answer_start_timestamp=record.answer_start_timestamp or datetime.now(),
            answer_start_unix=record.answer_start_unix or 0,
            answer_end_timestamp=record.answer_end_timestamp or datetime.now(),
            answer_end_unix=record.answer_end_unix or 0
        )
        mark("build_response")

        total_ms = (time.perf_counter() - t0) * 1000

        # レスポンスヘッダ（Flutter 側で serverTiming に出せる）
        # 例: Server-Timing: db_select;dur=3.2, db_commit;dur=25.1, total;dur=40.0
        server_timing = ", ".join([f"{k};dur={v:.1f}" for k, v in timings.items()])
        server_timing += f", total;dur={total_ms:.1f}"
        response.headers["Server-Timing"] = server_timing
        response.headers["X-Request-Id"] = req_id

        # サーバログ（相関ID付きで1行にまとめる）
        print(
            f"[Perf][update_answer] req_id={req_id} "
            f"answer_id={lesson_answer_data_id} "
            + " ".join([f"{k}={v:.1f}ms" for k, v in timings.items()])
            + f" total={total_ms:.1f}ms"
        )

        return res

    except Exception as e:
        total_ms = (time.perf_counter() - t0) * 1000
        print(f"[Perf][update_answer][ERROR] req_id={req_id} total={total_ms:.1f}ms err={e}")
        raise



# @router.put("/", response_model=LessonAnswerDataResponse)
# async def update_answer_data_by_id( # ★ 3. async def に変更
#     background_tasks: BackgroundTasks, # ★ 4. BackgroundTasks を依存関係として追加
#     lesson_answer_data_id: int = Query(..., description="更新対象の answer_data_id"),
#     update: LessonAnswerUpdateRequest = Body(...),
#     db: Session = Depends(get_db)
# ):
#     # レコード取得
#     record = db.query(LessonAnswerDataTable).filter(
#         LessonAnswerDataTable.lesson_answer_data_id == lesson_answer_data_id
#     ).first()

#     if not record:
#         raise HTTPException(status_code=404, detail="Answer data not found.")

#     # nullの場合は更新スキップ（かつUNIX時刻自動算出対応）
#     if update.choice_number is not None:
#         record.choice_number = update.choice_number

#     if update.answer_correctness is not None:
#         record.answer_correctness = update.answer_correctness

#     if update.answer_status is not None:
#         record.answer_status = update.answer_status

#     if update.answer_start_timestamp is not None:
#         record.answer_start_timestamp = update.answer_start_timestamp
#         record.answer_start_unix = int(update.answer_start_timestamp.timestamp())

#     elif update.answer_start_unix is not None:
#         record.answer_start_unix = update.answer_start_unix

#     if update.answer_end_timestamp is not None:
#         record.answer_end_timestamp = update.answer_end_timestamp
#         record.answer_end_unix = int(update.answer_end_timestamp.timestamp())

#     elif update.answer_end_unix is not None:
#         record.answer_end_unix = update.answer_end_unix

#     # DB反映
#     db.commit()
#     db.refresh(record)

#     # ★ 5. 【解決策】DB更新後、Socket.IOで教員側に通知
#     # 生徒のログから、教員側は 'from_flutter' イベントをリッスンしていることがわかる
#     if record.lesson_id:
#         # 新しいイベント形式: 'student_answered,lessonId,studentId,answerDataId'
#         emit_data = f"student_answered,{record.lesson_id},{record.student_id},{record.lesson_answer_data_id}"
        
#         # バックグラウンドタスクとして非同期のemitを実行
#         background_tasks.add_task(emit_to_web, 'from_flutter', emit_data)
#         print(f"Socket.IO emit Queued: {emit_data}")

#     # 既存のレスポンスを返す
#     return LessonAnswerDataResponse(
#         lesson_answer_data_id=record.lesson_answer_data_id,
#         student_id=record.student_id,
#         lesson_id=record.lesson_id or 0,
#         lesson_theme_id=record.lesson_theme_id or 0,
#         lesson_question_id=record.lesson_question_id,
#         choice_number=record.choice_number or 0,
#         answer_correctness=int(record.answer_correctness) if record.answer_correctness is not None else 0,
#         answer_status=record.answer_status or 0,
#         answer_start_timestamp=record.answer_start_timestamp or datetime.now(),
#         answer_start_unix=record.answer_start_unix or 0,
#         answer_end_timestamp=record.answer_end_timestamp or datetime.now(),
#         answer_end_unix=record.answer_end_unix or 0
#     # 