# routers/lesson_attendance.py
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import (
    LessonTable, TimetableTable, LessonRegistrationTable,
    LessonThemesTable, UnitTable, MaterialsTable, AttendanceTable
)
from schemas import LessonCalendarResponse, LessonInformationResponse, AttendanceCreate, LessonThemeBlock  # 後述

from typing import List
import asyncio

router = APIRouter(
    prefix="/lesson_attendance",
    tags=["lesson_attendance"]
)

from sqlalchemy.exc import IntegrityError







#生徒のスマホアプリ。講義からカレンダーに入る
@router.get("/calendar", response_model=List[LessonCalendarResponse])  # ✅ エンドポイント変更
def get_lesson_attendance_calendar(db: Session = Depends(get_db)):
    results = (
        db.query(
            TimetableTable.timetable_id,
            TimetableTable.date,
            TimetableTable.day_of_week,
            TimetableTable.period,
            TimetableTable.time,
            LessonTable.lesson_id,
            LessonTable.class_id,
            LessonTable.lesson_name,
            LessonTable.delivery_status,
            LessonTable.lesson_status,
        )
        .join(LessonTable, TimetableTable.timetable_id == LessonTable.timetable_id)
        .all()
    )
    return results

#生徒のスマホアプリ。カレンダーから授業受講できるようになる
@router.get("/lesson_information", response_model=LessonInformationResponse)
def get_lesson_information(lesson_id: int = Query(...), db: Session = Depends(get_db)):
    query_results = (
        db.query(
            LessonTable.class_id,
            LessonTable.timetable_id,
            LessonTable.lesson_name,
            LessonTable.delivery_status,
            LessonTable.lesson_status,
            TimetableTable.date,
            TimetableTable.day_of_week,
            TimetableTable.period,
            TimetableTable.time,
            LessonRegistrationTable.lesson_registration_id,
            LessonRegistrationTable.lesson_theme_id,
            LessonThemesTable.lecture_video_id,
            LessonThemesTable.textbook_id,
            LessonThemesTable.document_id,
            LessonThemesTable.lesson_theme_name,
            UnitTable.units_id,
            UnitTable.part_name,
            UnitTable.chapter_name,
            UnitTable.unit_name,
            MaterialsTable.material_id,
            MaterialsTable.material_name
        )
        .join(TimetableTable, LessonTable.timetable_id == TimetableTable.timetable_id)
        .join(LessonRegistrationTable, LessonTable.lesson_id == LessonRegistrationTable.lesson_id)
        .join(LessonThemesTable, LessonRegistrationTable.lesson_theme_id == LessonThemesTable.lesson_theme_id)
        .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id)
        .join(MaterialsTable, UnitTable.material_id == MaterialsTable.material_id)
        .filter(LessonTable.lesson_id == lesson_id)
        .all()
    )

    if not query_results:
        raise HTTPException(status_code=404, detail="Lesson not found")

    common_fields = dict(zip([
        "class_id", "timetable_id", "lesson_name",
        "delivery_status", "lesson_status",
        "date", "day_of_week", "period", "time"
    ], query_results[0][0:9]))

    lesson_theme_list = [
        LessonThemeBlock(**dict(zip([
            "lesson_registration_id", "lesson_theme_id",
            "lecture_video_id", "textbook_id", "document_id", "lesson_theme_name",
            "units_id", "part_name", "chapter_name", "unit_name",
            "material_id", "material_name"
        ], row[9:])))
        for row in query_results
    ]

    return LessonInformationResponse(**common_fields, lesson_theme=lesson_theme_list)



#先生の管理アプリと生徒のスマホアプリ。授業のステータスを変える
# WebSocket管理
active_connections: List[WebSocket] = []

@router.websocket("/ws/lesson_status")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

async def broadcast_lesson_status_update(lesson_id: int):
    message = {"event": "lesson_status_updated", "lesson_id": lesson_id}
    for conn in active_connections:
        await conn.send_json(message)



@router.put("/lesson_information", response_model=LessonInformationResponse)
def update_lesson_status_and_get_info(
    background_tasks: BackgroundTasks,
    lesson_id: int = Query(...),
    db: Session = Depends(get_db)
):
    # ① 授業取得
    lesson = db.query(LessonTable).filter(LessonTable.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # ② ステータス更新
    lesson.lesson_status = True
    db.commit()
    db.refresh(lesson)
    background_tasks.add_task(broadcast_lesson_status_update, lesson_id)

    # ③ 授業テーマ・登録情報取得（lesson_registration_id を含む）
    themes = (
        db.query(
            LessonRegistrationTable.lesson_registration_id,
            LessonThemesTable.lesson_theme_id,
            LessonThemesTable.lecture_video_id,
            LessonThemesTable.textbook_id,
            LessonThemesTable.document_id,
            LessonThemesTable.lesson_theme_name,
            LessonThemesTable.units_id,
            UnitTable.part_name,
            UnitTable.chapter_name,
            UnitTable.unit_name,
            MaterialsTable.material_id,
            MaterialsTable.material_name
        )
        .join(LessonThemesTable, LessonRegistrationTable.lesson_theme_id == LessonThemesTable.lesson_theme_id)
        .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id)
        .join(MaterialsTable, UnitTable.material_id == MaterialsTable.material_id)
        .filter(LessonRegistrationTable.lesson_id == lesson_id)
        .all()
    )

    # ④ Pydanticモデルに変換
    lesson_theme_blocks = [
        LessonThemeBlock(
            lesson_registration_id=row[0],
            lesson_theme_id=row[1],
            lecture_video_id=row[2],
            textbook_id=row[3],
            document_id=row[4],
            lesson_theme_name=row[5],
            units_id=row[6],
            part_name=row[7],
            chapter_name=row[8],
            unit_name=row[9],
            material_id=row[10],
            material_name=row[11],
        )
        for row in themes
    ]

    # ⑤ 時間割情報取得
    timetable = db.query(TimetableTable).filter(TimetableTable.timetable_id == lesson.timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")

    # ⑥ 結果返却
    return LessonInformationResponse(
        class_id=lesson.class_id,
        timetable_id=lesson.timetable_id,
        lesson_name=lesson.lesson_name,
        delivery_status=lesson.delivery_status,
        lesson_status=lesson.lesson_status,
        date=timetable.date,
        day_of_week=timetable.day_of_week,
        period=timetable.period,
        time=timetable.time,
        lesson_theme=lesson_theme_blocks
    )


# @router.put("/lesson_information", response_model=LessonInformationResponse)
# def update_lesson_status_and_get_info(
#     background_tasks: BackgroundTasks,
#     lesson_id: int = Query(...),
#     db: Session = Depends(get_db)
# ):
#     # 授業取得とステータス更新
#     lesson = db.query(LessonTable).filter(LessonTable.lesson_id == lesson_id).first()
#     if not lesson:
#         raise HTTPException(status_code=404, detail="Lesson not found")

#     lesson.lesson_status = True
#     db.commit()
#     db.refresh(lesson)
#     background_tasks.add_task(broadcast_lesson_status_update, lesson_id)

#     # 授業テーマ情報の取得（修正済み）
#     themes = (
#         db.query(
#             LessonRegistrationTable.lesson_registration_id,  # ✅ 追加

#             LessonThemesTable.lesson_theme_id,
#             LessonThemesTable.lecture_video_id,
#             LessonThemesTable.textbook_id,
#             LessonThemesTable.document_id,
#             LessonThemesTable.lesson_theme_name,
#             LessonThemesTable.units_id,
#             UnitTable.part_name,
#             UnitTable.chapter_name,
#             UnitTable.unit_name,
#             MaterialsTable.material_id,
#             MaterialsTable.material_name,

#         )
#         .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id)
#         .join(MaterialsTable, UnitTable.material_id == MaterialsTable.material_id)
#         .join(LessonRegistrationTable, LessonThemesTable.lesson_theme_id == LessonRegistrationTable.lesson_theme_id)
#         .filter(LessonRegistrationTable.lesson_id == lesson_id)
#         .all()
#     )

#     lesson_theme_blocks = [
#         LessonThemeBlock(
#             lesson_theme_id=row[0],
#             lecture_video_id=row[1],
#             textbook_id=row[2],
#             document_id=row[3],
#             lesson_theme_name=row[4],
#             units_id=row[5],
#             part_name=row[6],
#             chapter_name=row[7],
#             unit_name=row[8],
#             material_id=row[9],
#             material_name=row[10],
#         )
#         for row in themes
#     ]

#     # 時間割情報の取得
#     timetable = db.query(TimetableTable).filter(TimetableTable.timetable_id == lesson.timetable_id).first()

#     return LessonInformationResponse(
#         class_id=lesson.class_id,
#         timetable_id=lesson.timetable_id,
#         lesson_name=lesson.lesson_name,
#         delivery_status=lesson.delivery_status,
#         lesson_status=lesson.lesson_status,
#         date=timetable.date,
#         day_of_week=timetable.day_of_week,
#         period=timetable.period,
#         time=timetable.time,
#         lesson_theme=lesson_theme_blocks
#     )

@router.put("/lesson_information/attendance")
def update_attendance_status(
    student_id: int = Query(...),
    lesson_id: int = Query(...),
    db: Session = Depends(get_db)
):
    # 出席レコードの取得
    record = (
        db.query(AttendanceTable)
        .filter(
            AttendanceTable.student_id == student_id,
            AttendanceTable.lesson_id == lesson_id
        )
        .first()
    )

    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")

    # ステータス更新
    if record.attendance_status is False:
        record.attendance_status = True
        db.commit()
        db.refresh(record)

    return {
        "attendance_id": record.attendance_id,
        "student_id": record.student_id,
        "lesson_id": record.lesson_id,
        "attendance_status": record.attendance_status
    }
