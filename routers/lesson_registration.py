from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from models import MaterialTable, UnitTable, LessonThemesTable, TimetableTable, LessonTable, LessonRegistrationTable, ClassTable
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

router = APIRouter(
    prefix="/lesson_registrations",
    tags=["lesson_registration"]
)

@router.post("/calendar", response_model=TimetableResponse)
def create_timetable_entry(
    timetable_data: TimetableCreate, db: Session = Depends(get_db)
):
    """
    時間割をpostする。
    """
    try:
        logger.info(f"リクエストデータ: {timetable_data}")
        
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
            return jsonable_encoder(existing_entry)
        
        # 新規作成
        new_entry = TimetableTable(**timetable_data.dict())
        db.add(new_entry)
        db.commit()
        db.refresh(new_entry)
        
        logger.info(f"新規登録完了: {new_entry}")
        return jsonable_encoder(new_entry)
    except Exception as e:
        logger.error(f"エラー発生: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/all")
def get_all_lesson_data(db: Session = Depends(get_db)):
    """
    materials_table, units_table, lesson_themes_table の全データを取得
    """
    try:
        logger.info("全ての教材データを取得開始")
        
        materials = db.query(MaterialTable).all()
        units = db.query(UnitTable).all()
        lesson_themes = db.query(LessonThemesTable).all()
        
        if not materials and not units and not lesson_themes:
            logger.warning("取得できるデータがありません")
            return {"message": "No data available"}
        
        # SQLAlchemy オブジェクトを辞書型に変換
        materials_list = [m.__dict__ for m in materials]
        units_list = [u.__dict__ for u in units]
        lesson_themes_list = [lt.__dict__ for lt in lesson_themes]
        
        # _sa_instance_state を削除
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
        
        # lesson_table に新規授業を登録
        new_lesson = LessonTable(
            class_id=lesson_data.class_id,
            timetable_id=lesson_data.timetable_id,
            lesson_name="物理",
            lesson_status=1     # READY
        )
        db.add(new_lesson)
        db.commit()
        db.refresh(new_lesson)
        
        # 各 lesson_theme_id に対して登録を作成
        registrations = []
        for theme_id in lesson_data.lesson_theme_ids:
            registration = LessonRegistrationTable(
                lesson_id=new_lesson.lesson_id,
                lesson_theme_id=theme_id,
                lesson_question_status=1  # NOT_STARTED
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

@router.get("/calendar", response_model=List[LessonRegistrationCalendarResponse])
def get_lesson_registration_calendar(
    class_id: Optional[int] = Query(None, description="クラスID（オプション）"),
    academic_year: Optional[int] = Query(None, description="年度（オプション）"),
    db: Session = Depends(get_db)
):
    """
    授業カレンダーを取得。
    class_idやacademic_yearが指定された場合は、その条件で授業を絞り込む。
    成績表示画面で使用。
    """
    query = (
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
            ClassTable.class_name,
            ClassTable.grade,
        )
        .join(LessonTable, TimetableTable.timetable_id == LessonTable.timetable_id, isouter=True)
        .join(ClassTable, LessonTable.class_id == ClassTable.class_id, isouter=True)
    )
    
    # academic_yearが指定されていればフィルタリング
    if academic_year is not None:
        query = query.filter(ClassTable.academic_year == academic_year)
    
    # class_idが指定されていればフィルタリング
    if class_id is not None:
        query = query.filter(LessonTable.class_id == class_id)
    
    results = query.all()
    
    # レスポンス形式に変換
    response = []
    for row in results:
        response.append(LessonRegistrationCalendarResponse(
            timetable_id=row[0],
            date=row[1],
            day_of_week=row[2],
            period=row[3],
            time=row[4],
            lesson_id=row[5],
            class_id=row[6] or 0,
            lesson_name=row[7],
            delivery_status=False,
            lesson_status=bool(row[8] == 2 or row[8] == 3) if row[8] else False,
            class_name=row[9] or "",
            grade=row[10] or 0
        ))
    
    return response
