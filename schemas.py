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
    lesson_theme_id: int

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
    units_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class LessonThemeWithVideos(LessonThemeBase):
    lecture_videos: List[LectureVideo] = []
    
    class Config:
        from_attributes = True

# -------------------------------
# 単元（Unit）と授業テーマ
# -------------------------------
class UnitBase(BaseModel):
    units_id: int
    material_id: Optional[int] = None
    part_name: Optional[str] = None
    chapter_name: Optional[str] = None
    unit_name: Optional[str] = None
    
    class Config:
        from_attributes = True

class UnitWithThemes(UnitBase):
    lesson_themes: List[LessonThemeWithVideos] = []
    
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
# クラス（新規追加）
# -------------------------------
class ClassResponse(BaseModel):
    class_id: int
    class_name: str
    grade: int
    teacher: Optional[str] = None
    academic_year: Optional[int] = None
    
    class Config:
        from_attributes = True

# -------------------------------
# 授業登録
# -------------------------------
class LessonRegistrationCreate(BaseModel):
    class_id: int
    timetable_id: int
    lesson_theme_ids: List[int]

class LessonRegistrationResponse(BaseModel):
    lesson_id: int
    lesson_registration_id: int

class LessonRegistrationCalendarResponse(BaseModel):
    timetable_id: int
    date: date
    day_of_week: str
    period: int
    time: str
    lesson_id: Optional[int] = None
    class_id: Optional[int] = None
    lesson_name: Optional[str] = None
    delivery_status: bool = False
    lesson_status: bool = False
    class_name: Optional[str] = None
    grade: Optional[int] = None
    
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
    class_name: Optional[str] = None
    lesson_name: Optional[str] = None
    delivery_status: bool = False
    lesson_status: bool = False
    
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
    part_name: Optional[str] = None
    chapter_name: Optional[str] = None
    unit_name: Optional[str] = None
    material_id: int
    material_name: str
    
    class Config:
        from_attributes = True

class LessonInformationResponse(BaseModel):
    class_id: int
    timetable_id: int
    lesson_name: Optional[str] = None
    delivery_status: Optional[bool] = False
    lesson_status: Optional[bool] = False
    date: date
    day_of_week: str
    period: int
    time: str
    lesson_theme: List[LessonThemeBlock] = []
    
    class Config:
        from_attributes = True

# -------------------------------
# 出席登録
# -------------------------------
class AttendanceCreate(BaseModel):
    student_id: int
    lesson_id: int

# -------------------------------
# 成績表示用（新規追加）
# -------------------------------
class StudentInfo(BaseModel):
    student_id: int
    name: str
    class_id: int
    students_number: int

class QuestionInfo(BaseModel):
    question_id: int
    question_label: str
    correct_choice: str
    part_name: Optional[str] = None
    chapter_name: Optional[str] = None
    unit_name: Optional[str] = None
    lesson_theme_name: Optional[str] = None

class AnswerInfo(BaseModel):
    selected_choice: Optional[str] = None
    is_correct: Optional[bool] = None
    start_unix: Optional[int] = None
    end_unix: Optional[int] = None

class GradesRawDataItem(BaseModel):
    student: StudentInfo
    question: QuestionInfo
    answer: AnswerInfo

class StudentComment(BaseModel):
    student_id: int
    student_name: str
    comment_text: Optional[str] = None

class GradesCommentsResponse(BaseModel):
    lesson_id: int
    comments: List[StudentComment] = []

# -------------------------------
# lesson_answer_data用（DB構造に合わせて追加）
# -------------------------------
class LessonQuestionResponse(BaseModel):
    lesson_question_id: int
    lesson_question_label: Optional[str] = None
    question_text1: Optional[str] = None
    question_text2: Optional[str] = None
    question_text3: Optional[str] = None
    question_text4: Optional[str] = None
    correctness_number: Optional[int] = None

class LessonAnswerDataResponse(BaseModel):
    lesson_answer_data_id: int
    student_id: int
    lesson_id: Optional[int] = None
    lesson_theme_id: Optional[int] = None
    lesson_question_id: int
    choice_number: Optional[int] = None
    answer_correctness: Optional[bool] = None
    answer_status: Optional[int] = None
    answer_start_timestamp: Optional[datetime] = None
    answer_start_unix: Optional[int] = None
    answer_end_timestamp: Optional[datetime] = None
    answer_end_unix: Optional[int] = None

class LessonAnswerDataWithDetails(BaseModel):
    lesson_answer_data_id: int
    student_id: int
    lesson_id: Optional[int] = None
    lesson_theme_id: Optional[int] = None
    choice_number: Optional[int] = None
    answer_correctness: Optional[int] = None
    answer_status: Optional[int] = None
    answer_start_timestamp: Optional[datetime] = None
    answer_start_unix: Optional[int] = None
    answer_end_timestamp: Optional[datetime] = None
    answer_end_unix: Optional[int] = None
    question: LessonQuestionResponse

class LessonAnswerUpdateRequest(BaseModel):
    choice_number: Optional[int] = None
    answer_correctness: Optional[int] = None
    answer_status: Optional[int] = None
    answer_start_timestamp: Optional[datetime] = None
    answer_start_unix: Optional[int] = None
    answer_end_timestamp: Optional[datetime] = None
    answer_end_unix: Optional[int] = None

# -------------------------------
# 既存のスキーマ（互換性のため）
# -------------------------------
# class AnswerData(BaseModel):
#     answer_data_id: int
#     student_id: int
#     lesson_id: int
#     lesson_theme_id: int
#     question_id: int
#     answer: str
#     answer_correctness: int
#     answer_status: int
#     answer_start_timestamp: datetime
#     answer_start_unix: int
#     answer_end_timestamp: datetime
#     answer_end_unix: int

class AnswerDataWithDetails(BaseModel):
    student_id: int
    lesson_id: int
    answer_correctness: Optional[int] = None
    answer_status: Optional[int] = None
    answer_start_unix: Optional[int] = None
    answer_end_unix: Optional[int] = None
    question: dict
    
    class Config:
        from_attributes = True

class AnswerUpdateRequest(BaseModel):
    answer_correctness: Optional[int] = None
    answer_status: Optional[int] = None
    answer_start_timestamp: Optional[datetime] = None
    answer_start_unix: Optional[int] = None
    answer_end_timestamp: Optional[datetime] = None
    answer_end_unix: Optional[int] = None

class AnswerDataRealtimeResponse(BaseModel):
    answer_data_id: int
    student_id: int
    lesson_theme_id: int
    question_id: int
    answer: Optional[str] = None
    answer_correctness: Optional[bool] = None
    answer_status: Optional[int] = None
    
    class Config:
        from_attributes = True

class AnswerDataBulkResponse(BaseModel):
    answer_data_id: int
    student_id: int
    lesson_id: int
    lesson_theme_id: int
    question_id: int
    answer: Optional[str] = None
    answer_correctness: Optional[bool] = None
    answer_status: int

class BulkInsertResponse(BaseModel):
    lesson_id: int
    lesson_name: str
    total_students: int
    total_questions: int
    total_answer_data: int
    answer_data_list: List[AnswerDataBulkResponse]
    message: str

class LessonAnswerDataBulkResponse(BaseModel):
    lesson_answer_data_id: int
    student_id: int
    lesson_id: int
    lesson_theme_id: int
    lesson_question_id: int

# 既存システム用の追加スキーマ
class QuestionDetail(BaseModel):
    question_id: int
    question_type: str
    question_label: str
    question_text: str
    question_image_url: Optional[str] = None
    choices: List['Choice'] = []
    answers: List['Answer'] = []

class Choice(BaseModel):
    choice_id: int
    choice_number: int
    choice_text: str
    answer_correctness: int
    choice_image_url: Optional[str] = None

class Answer(BaseModel):
    answer_id: int
    answer_name: str
    answer_text: str
    answer_image_url: Optional[str] = None

class LessonThemeDetail(BaseModel):
    lesson_theme_id: int
    exercise_flag: bool
    exercise_status: str