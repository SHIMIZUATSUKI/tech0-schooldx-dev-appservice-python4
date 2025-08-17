####### schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime

# -------------------------------
# 講義動画
# -------------------------------
class LectureVideoBase(BaseModel):
    lecture_video_title: str
    video_url: str

class LectureVideoCreate(BaseModel):
    lesson_theme_id: int  # タイトルはAPI側で自動生成

class LectureVideo(LectureVideoBase):
    lecture_video_id: int
    lesson_theme_id: int

    class Config:
        from_attributes = True


# -------------------------------
# 授業テーマ（LessonTheme）と動画
# -------------------------------
class LessonThemeBase(BaseModel):
    lesson_theme_id: int
    lesson_theme_name: str
    units_id: Optional[int] = None  # 必要に応じて

    class Config:
        from_attributes = True

class LessonThemeWithVideos(LessonThemeBase):
    lecture_videos: List[LectureVideo]

    class Config:
        from_attributes = True


# -------------------------------
# 単元（Unit）と授業テーマ
# -------------------------------
class UnitBase(BaseModel):
    units_id: int
    material_id: Optional[int] = None
    part_name: Optional[str]
    chapter_name: Optional[str]
    unit_name: Optional[str]

    class Config:
        from_attributes = True

class UnitWithThemes(UnitBase):
    lesson_themes: List[LessonThemeWithVideos]

    class Config:
        from_attributes = True


# -------------------------------
# 時間割（Timetable）
# -------------------------------
class TimetableBase(BaseModel):
    date: date
    day_of_week: str = Field(..., max_length=10)
    period: int
    time: str = Field(..., max_length=11)

class TimetableCreate(TimetableBase):
    pass

class TimetableResponse(TimetableBase):
    timetable_id: int

    class Config:
        from_attributes = True


# -------------------------------
# 教材（Material）と単元
# -------------------------------
class MaterialBase(BaseModel):
    material_id: int
    material_name: str

class MaterialWithUnits(MaterialBase):
    units: List[UnitWithThemes]

    class Config:
        from_attributes = True


# -------------------------------
# 授業登録
# -------------------------------
class LessonRegistrationCreate(BaseModel):
    class_id: int
    timetable_id: int
    lesson_theme_ids: List[int]  # ← 配列にする


class LessonRegistrationResponse(BaseModel):
    lesson_id: int
    lesson_registration_id: int

class LessonRegistrationCalendarResponse(BaseModel):
    timetable_id: int
    date: date
    day_of_week: str
    period: int
    time: str
    lesson_id: int
    class_id: int
    lesson_name: Optional[str]
    delivery_status: bool
    lesson_status: bool
    class_name: str
    grade: int

    class Config:
        from_attributes = True


# -------------------------------
# 授業カレンダー（受講者用）
# -------------------------------
class LessonCalendarResponse(BaseModel):
    timetable_id: int
    date: date
    day_of_week: str
    period: int
    time: str
    lesson_id: int
    class_id: int
    lesson_name: Optional[str]
    delivery_status: bool
    lesson_status: bool

    class Config:
        from_attributes = True


# -------------------------------
# 授業情報（詳細表示）
# -------------------------------
class LessonThemeBlock(BaseModel):
    lesson_registration_id: int
    lesson_theme_id: int
    lecture_video_id: int
    textbook_id: int
    document_id: int
    lesson_theme_name: str
    units_id: int
    part_name: Optional[str]
    chapter_name: Optional[str]
    unit_name: Optional[str]
    material_id: int
    material_name: str


    class Config:
        from_attributes = True

class LessonInformationResponse(BaseModel):
    class_id: int
    timetable_id: int
    lesson_name: Optional[str]
    delivery_status: Optional[bool]
    lesson_status: Optional[bool]
    date: date
    day_of_week: str
    period: int
    time: str
    lesson_theme: List[LessonThemeBlock]

    class Config:
        from_attributes = True


# -------------------------------
# 出席登録
# -------------------------------
class AttendanceCreate(BaseModel):
    student_id: int
    lesson_id: int


# -------------------------------
# 問題・選択肢・正解
# -------------------------------
class Choice(BaseModel):
    choice_id: int
    choice_number: int
    choice_text: str
    answer_correctness: int
    choice_image_url: Optional[str]

class Answer(BaseModel):
    answer_id: int
    answer_name: str
    answer_text: Optional[str]
    answer_image_url: Optional[str]

class QuestionDetail(BaseModel):
    question_id: int
    question_type: str
    question_label: str
    question_text: Optional[str]
    question_image_url: Optional[str]
    choices: List[Choice]
    answers: List[Answer]


# -------------------------------
# 回答データ詳細付き
# -------------------------------
class LessonThemeDetail(BaseModel):
    lesson_theme_id: int
    exercise_flag: Optional[bool]
    exercise_status: Optional[str]

class AnswerDataWithDetails(BaseModel):
    answer_data_id: int
    student_id: int
    lesson_id: int
    lesson_theme: LessonThemeDetail
    answer: str
    answer_correctness: int
    answer_status: int
    answer_start_timestamp: datetime
    answer_start_unix: int
    answer_end_timestamp: datetime
    answer_end_unix: int
    question: QuestionDetail

    class Config:
        from_attributes = True


# -------------------------------
# 回答データ
# -------------------------------
class AnswerData(BaseModel):
    answer_data_id: int
    student_id: int
    lesson_id: int
    lesson_theme_id: int
    question_id: int
    answer: str
    answer_correctness: int
    answer_status: int
    answer_start_timestamp: datetime
    answer_start_unix: int
    answer_end_timestamp: datetime
    answer_end_unix: int

    class Config:
        from_attributes = True

class AnswerUpdateRequest(BaseModel):
    answer_correctness: Optional[int] = None
    answer_status: Optional[int] = None
    answer_start_timestamp: Optional[datetime] = None
    answer_start_unix: Optional[int] = None
    answer_end_timestamp: Optional[datetime] = None
    answer_end_unix: Optional[int] = None

# -------------------------------
# 回答データ（リアルタイム取得用）
# -------------------------------
class AnswerDataRealtimeResponse(BaseModel):
    answer_data_id: int
    student_id: int
    lesson_id: Optional[int] = None
    lesson_theme_id: Optional[int] = None
    question_id: int
    answer: Optional[str] = None
    answer_correctness: Optional[int] = None
    answer_status: Optional[int] = None
    answer_start_timestamp: Optional[datetime] = None
    answer_start_unix: Optional[int] = None
    answer_end_timestamp: Optional[datetime] = None
    answer_end_unix: Optional[int] = None

# -------------------------------
# 授業開始 → 回答データ一括作成
# -------------------------------
class StartLessonRequest(BaseModel):
    lesson_theme_id: int
    question_ids: List[int]

class AnswerDataBulkResponse(BaseModel):
    answer_data_id: int
    student_id: int
    lesson_id: int
    lesson_theme_id: int
    question_id: int
    answer: Optional[str] = None
    answer_correctness: Optional[bool] = None
    answer_status: int = 0
    answer_start_timestamp: Optional[datetime] = None
    answer_start_unix: Optional[int] = None
    answer_end_timestamp: Optional[datetime] = None
    answer_end_unix: Optional[int] = None

    class Config:
        from_attributes = True

class BulkInsertResponse(BaseModel):
    lesson_id: int
    lesson_name: str
    total_students: int
    total_questions: int
    total_answer_data: int
    answer_data_list: List[AnswerDataBulkResponse]
    message: str
