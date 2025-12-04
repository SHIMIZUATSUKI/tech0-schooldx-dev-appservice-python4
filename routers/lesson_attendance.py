# routers/lesson_attendance.py
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from models import (
    LessonTable, TimetableTable, LessonRegistrationTable,
    LessonThemesTable, UnitTable, MaterialTable, AttendanceTable,
    ClassTable,LessonThemeContentsTable
)
from schemas import LessonCalendarResponse, LessonInformationResponse, AttendanceCreate, LessonThemeBlock
from typing import List
from sqlalchemy import func

router = APIRouter(
    prefix="/lesson_attendance",
    tags=["lesson_attendance"]
)

@router.get("/calendar", response_model=List[LessonCalendarResponse])
def get_lesson_attendance_calendar(db: Session = Depends(get_db)):
    """
    生徒のスマホアプリ。講義からカレンダーに入る
    """
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
            LessonTable.lesson_status,
            ClassTable.class_name, # class_name を取得
        )
        .join(LessonTable, TimetableTable.timetable_id == LessonTable.timetable_id)
        .join(ClassTable, LessonTable.class_id == ClassTable.class_id) # ClassTableをJOIN
        .all()
    )
    
    # delivery_statusは別途取得する必要がある場合は追加
    response = []
    for row in results:
        response.append(LessonCalendarResponse(
            timetable_id=row.timetable_id,
            date=row.date,
            day_of_week=row.day_of_week,
            period=row.period,
            time=row.time,
            lesson_id=row.lesson_id,
            class_id=row.class_id,
            lesson_name=row.lesson_name,
            class_name=row.class_name,
            delivery_status=False,
            lesson_status=bool(row.lesson_status == 2 or row.lesson_status == 3) if row.lesson_status else False
        ))
    
    return response

@router.get("/lesson_information", response_model=LessonInformationResponse)
def get_lesson_information(lesson_id: int = Query(...), db: Session = Depends(get_db)):
    """
    生徒のスマホアプリ。カレンダーから授業受講できるようになる
    """
    query_results = (
        db.query(
            LessonTable.class_id,
            LessonTable.timetable_id,
            LessonTable.lesson_name,
            LessonTable.lesson_status,
            TimetableTable.date,
            TimetableTable.day_of_week,
            TimetableTable.period,
            TimetableTable.time,
            LessonRegistrationTable.lesson_registration_id,
            LessonRegistrationTable.lesson_theme_id,
            LessonThemesTable.lesson_theme_name,
            UnitTable.units_id,
            UnitTable.part_name,
            UnitTable.chapter_name,
            UnitTable.unit_name,
            MaterialTable.material_id,
            MaterialTable.material_name,
            # LessonThemeContentsTable.lesson_question_status,
            LessonRegistrationTable.lesson_question_status  # 20251126 テーブルを変更
        )
        .join(TimetableTable, LessonTable.timetable_id == TimetableTable.timetable_id)
        .join(LessonRegistrationTable, LessonTable.lesson_id == LessonRegistrationTable.lesson_id)
        .join(LessonThemesTable, LessonRegistrationTable.lesson_theme_id == LessonThemesTable.lesson_theme_id)
        .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id)
        .join(MaterialTable, UnitTable.material_id == MaterialTable.material_id)
        # .join(LessonThemeContentsTable, LessonThemesTable.lesson_theme_contents_id == LessonThemeContentsTable.lesson_theme_contents_id)  # 20251110追加→再削除
        .filter(LessonTable.lesson_id == lesson_id)
        .all()
    )
    
    if not query_results:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    common_fields = dict(zip([
        "class_id", "timetable_id", "lesson_name", "lesson_status",
        "date", "day_of_week", "period", "time"
    ], [query_results[0][0], query_results[0][1], query_results[0][2],
        bool(query_results[0][3] == 2 or query_results[0][3] == 3) if query_results[0][3] else False,
        query_results[0][4], query_results[0][5], query_results[0][6], query_results[0][7]]))
    
    # delivery_statusは仮の値
    common_fields["delivery_status"] = False
    
    lesson_theme_list = []
    for row in query_results:
        lesson_theme_list.append(LessonThemeBlock(
            lesson_registration_id=row[8],
            lesson_theme_id=row[9],
            lesson_question_status=row[17],         # 20251110追加
            lecture_video_id=0,
            textbook_id=0,
            document_id=0,
            lesson_theme_name=row[10],
            units_id=row[11],
            part_name=row[12],
            chapter_name=row[13],
            unit_name=row[14],
            material_id=row[15],
            material_name=row[16]
        ))
    
    return LessonInformationResponse(**common_fields, lesson_theme=lesson_theme_list)

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
    # 授業取得
    lesson = db.query(LessonTable).filter(LessonTable.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    # ステータス更新
    lesson.lesson_status = 2  # ACTIVE
    db.commit()
    db.refresh(lesson)
    
    background_tasks.add_task(broadcast_lesson_status_update, lesson_id)
    
    # 授業テーマ・登録情報取得
    themes = (
        db.query(
            LessonRegistrationTable.lesson_registration_id,
            LessonThemesTable.lesson_theme_id,
            LessonThemesTable.lesson_theme_name,
            LessonThemesTable.units_id,
            UnitTable.part_name,
            UnitTable.chapter_name,
            UnitTable.unit_name,
            MaterialTable.material_id,
            MaterialTable.material_name
        )
        .join(LessonThemesTable, LessonRegistrationTable.lesson_theme_id == LessonThemesTable.lesson_theme_id)
        .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id)
        .join(MaterialTable, UnitTable.material_id == MaterialTable.material_id)
        .filter(LessonRegistrationTable.lesson_id == lesson_id)
        .all()
    )
    
    # Pydanticモデルに変換
    lesson_theme_blocks = [
        LessonThemeBlock(
            lesson_registration_id=row[0],
            lesson_theme_id=row[1],
            lecture_video_id=0,
            textbook_id=0,
            document_id=0,
            lesson_theme_name=row[2],
            units_id=row[3],
            part_name=row[4],
            chapter_name=row[5],
            unit_name=row[6],
            material_id=row[7],
            material_name=row[8],
        )
        for row in themes
    ]
    
    # 時間割情報取得
    timetable = db.query(TimetableTable).filter(TimetableTable.timetable_id == lesson.timetable_id).first()
    if not timetable:
        raise HTTPException(status_code=404, detail="Timetable not found")
    
    # 結果返却
    return LessonInformationResponse(
        class_id=lesson.class_id,
        timetable_id=lesson.timetable_id,
        lesson_name=lesson.lesson_name,
        delivery_status=False,
        lesson_status=bool(lesson.lesson_status == 2 or lesson.lesson_status == 3),
        date=timetable.date,
        day_of_week=timetable.day_of_week,
        period=timetable.period,
        time=timetable.time,
        lesson_theme=lesson_theme_blocks
    )

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