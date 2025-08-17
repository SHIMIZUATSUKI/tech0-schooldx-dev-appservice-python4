from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import MaterialsTable, UnitTable, LessonThemesTable, TimetableTable, LessonTable, LessonRegistrationTable, ClassTableTable
from schemas import (
    MaterialWithUnits, UnitWithThemes, LessonThemeBase, 
    TimetableCreate, TimetableResponse,
    LessonRegistrationResponse, LessonRegistrationCreate,
    LessonRegistrationCalendarResponse
)
from fastapi.encoders import jsonable_encoder
import logging

# ログの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ✅ APIRouterを1つに統一
router = APIRouter(
    prefix="/lesson_registrations",
    tags=["lesson_registration"]
)

# 1️⃣ 授業登録（時間割登録）
"""
    Azure MySQL に時間割をpostする。
"""
@router.post("/calendar", response_model=TimetableResponse)
def create_timetable_entry(
    timetable_data: TimetableCreate, db: Session = Depends(get_db)
):
    try:
        logger.info(f"リクエストデータ: {timetable_data}")

        # ✅ データベースセッションの確認
        if db is None:
            logger.error("データベースセッションが取得できませんでした")
            raise HTTPException(status_code=500, detail="Database connection error")

        # 既存の時間割エントリをチェック
        existing_entry = db.query(TimetableTable).filter(
            TimetableTable.date == timetable_data.date,
            TimetableTable.day_of_week == timetable_data.day_of_week,
            TimetableTable.period == timetable_data.period,
            TimetableTable.time == timetable_data.time
        ).first()

        if existing_entry:
            logger.info(f"既存エントリが見つかりました: {existing_entry}")
            return jsonable_encoder(existing_entry)  # ✅ JSON変換して返す

        # 新規作成
        new_entry = TimetableTable(**timetable_data.dict())
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)

        logger.info(f"新規登録完了: {new_entry}")
        return jsonable_encoder(new_entry)  # ✅ JSON変換して返す

    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

# 2️⃣ 授業登録時の教材・単元・授業テーマ取得
@router.get("/all")
def get_all_lesson_data(db: Session = Depends(get_db)):
    """
    Azure MySQL から `materials_table`, `units_table`, `lesson_themes_table` の全データを取得
    """
    try:
        logger.info("全ての教材データを取得開始")

        materials = db.query(MaterialsTable).all()
        units = db.query(UnitTable).all()
        lesson_themes = db.query(LessonThemesTable).all()

        if not materials and not units and not lesson_themes:
            logger.warning("取得できるデータがありません")
            return {"message": "No data available"}

        # ✅ SQLAlchemy オブジェクトを辞書型に変換
        materials_list = [m.__dict__ for m in materials]
        units_list = [u.__dict__ for u in units]
        lesson_themes_list = [lt.__dict__ for lt in lesson_themes]

        # ✅ SQLAlchemy の _sa_instance_state を削除
        for data in materials_list + units_list + lesson_themes_list:
            data.pop("_sa_instance_state", None)

        response = {
            "materials": materials_list,
            "units": units_list,
            "lesson_themes": lesson_themes_list
        }

        logger.info(f"取得データ: {response}")
        return jsonable_encoder(response)

    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 3️⃣ 授業内容を登録
@router.post("/", response_model=dict)
def register_lesson(
    lesson_data: LessonRegistrationCreate,
    db: Session = Depends(get_db)
):
    """
    授業と複数の授業テーマを登録するエンドポイント
    """
    try:
        logger.info(f"授業登録リクエスト: {lesson_data}")

        # ✅ lesson_table に新規授業を登録
        new_lesson = LessonTable(
            class_id=lesson_data.class_id,
            timetable_id=lesson_data.timetable_id,
            delivery_status=False,
            lesson_status=False
        )
        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)

        # ✅ 各 lesson_theme_id に対して登録を作成
        registrations = []
        for theme_id in lesson_data.lesson_theme_ids:
            registration = LessonRegistrationTable(
                lesson_id=new_lesson.lesson_id,
                lesson_theme_id=theme_id
            )
            db.add(registration)
            registrations.append(registration)

        db.commit()
        # 新規登録IDの一覧を取得
        db.refresh(new_lesson)
        for r in registrations:
            db.refresh(r)

        response = {
            "lesson_id": new_lesson.lesson_id,
            "lesson_registration_ids": [r.lesson_registration_id for r in registrations]
        }
        return jsonable_encoder(response)

    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


# 4️⃣ 授業登録カレンダーの取得
@router.get("/calendar", response_model=List[LessonRegistrationCalendarResponse])
def get_lesson_registration_calendar(db: Session = Depends(get_db)):
    try:
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
                ClassTableTable.class_name,
                ClassTableTable.grade,
            )
            .join(LessonTable, TimetableTable.timetable_id == LessonTable.timetable_id)
            .join(ClassTableTable, LessonTable.class_id == ClassTableTable.class_id)
            .all()
        )
        if not results:
            raise HTTPException(status_code=404, detail="No registration calendar data found")
        return results
    except Exception as e:
        logger.error(f"カレンダー取得エラー: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
