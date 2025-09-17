from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime, Text, Float, BigInteger
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

# 1. クラステーブル
class ClassTableTable(Base):
    __tablename__ = "class_table"
    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(255))
    grade = Column(Integer)
    students = relationship("StudentTable", back_populates="class_table")
    lessons = relationship("LessonTable", back_populates="class_table")
    notifications = relationship("NotificationTable", back_populates="class_table")

# 2. 生徒テーブル
class StudentTable(Base):
    __tablename__ = "students_table"
    student_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("class_table.class_id"), nullable=False)
    name = Column(String(255))
    account_name = Column(String(255))
    mail_address = Column(String(255), unique=True)
    password = Column(String(255))

    # ユーザー管理用に追加
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    class_table = relationship("ClassTableTable", back_populates="students")
    attendances = relationship("AttendanceTable", back_populates="student")
    view_data = relationship("ViewDataTable", back_populates="student")
    answer_data = relationship("AnswerDataTable", back_populates="student")
    questions = relationship("StudentQuestionTable", back_populates="student")
    notification_reads = relationship("NotificationReadTable", back_populates="student")


# 3. 出席データテーブル（修正済み）
class AttendanceTable(Base):
    __tablename__ = "attendance_table"
    
    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)  # 🔼 追加された授業ID
    attendance_status = Column(Boolean)  # TINYINT(1) 相当 → BooleanでOK

    student = relationship("StudentTable", back_populates="attendances")
    lesson = relationship("LessonTable", back_populates="attendances")  # 🔼 新たに追加
   

# 4. 通知テーブル
class NotificationTable(Base):
    __tablename__ = "notifications_table"
    notification_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)
    class_id = Column(Integer, ForeignKey("class_table.class_id"), nullable=False)
    notification_category = Column(String(255))
    notification_title = Column(String(255))
    notification_body = Column(String(255))
    class_table = relationship("ClassTableTable", back_populates="notifications")
    notification_reads = relationship("NotificationReadTable", back_populates="notification")
    lesson = relationship("LessonTable", back_populates="notifications")  # ← これが正しい場所！


# 5. 授業テーブル
class LessonTable(Base):
    __tablename__ = "lessons_table"
    lesson_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("class_table.class_id"), nullable=False)
    timetable_id = Column(Integer, ForeignKey("timetable_table.timetable_id"), nullable=False)
    lesson_name = Column(String(255))
    delivery_status = Column(Boolean)
    lesson_status = Column(Boolean, default=False)

    #lesson_status = Column(Boolean)
     # 🔽 必須！これがないと mapper エラーになる
    timetable = relationship("TimetableTable", back_populates="lessons")

    class_table = relationship("ClassTableTable", back_populates="lessons")
    exercises = relationship("ExerciseTable", back_populates="lesson")
    view_data = relationship("ViewDataTable", back_populates="lesson")
    answer_data = relationship("AnswerDataTable", back_populates="lesson")
    questions = relationship("StudentQuestionTable", back_populates="lesson")
    registrations = relationship("LessonRegistrationTable", back_populates="lesson")
    notifications = relationship("NotificationTable", back_populates="lesson")
    attendances = relationship("AttendanceTable", back_populates="lesson")  # 🔼 新たに追加


# 6. 時間割テーブル
class TimetableTable(Base):
    __tablename__ = "timetable_table"
    timetable_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    day_of_week = Column(String(10))
    period = Column(Integer)
    time = Column(String(11))
    lessons = relationship("LessonTable", back_populates="timetable")

# 7. 教材テーブル
class MaterialsTable(Base):
    __tablename__ = "materials_table"
    material_id = Column(Integer, primary_key=True, autoincrement=True)
    material_name = Column(String(255))
    units = relationship("UnitTable", back_populates="material")
    textbooks = relationship("TextbookTable", back_populates="material")
    documents = relationship("DocumentTable", back_populates="material")
    questions = relationship("QuestionTable", back_populates="material")

# 8. 単元テーブル
class UnitTable(Base):
    __tablename__ = "units_table"
    units_id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials_table.material_id"), nullable=False)
    part_name = Column(String(255))
    chapter_name = Column(String(255))
    unit_name = Column(String(255))
    material = relationship("MaterialsTable", back_populates="units")
    lesson_themes = relationship("LessonThemesTable", back_populates="unit")

# 9. 授業コンテンツテーブル
class LessonThemesTable(Base):
    __tablename__ = "lesson_themes_table"
    lesson_theme_id = Column(Integer, primary_key=True, autoincrement=True)
    units_id = Column(Integer, ForeignKey("units_table.units_id"), nullable=False)
    lecture_video_id = Column(Integer, ForeignKey("lecture_videos_table.lecture_video_id"), nullable=False)
    textbook_id = Column(Integer, ForeignKey("textbooks_table.textbook_id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents_table.document_id"), nullable=False)
    lesson_theme_name = Column(String(255))
    unit = relationship("UnitTable", back_populates="lesson_themes")
    lecture_video = relationship("LectureVideosTable", back_populates="lesson_theme")
    textbook = relationship("TextbookTable", back_populates="lesson_themes")
    document = relationship("DocumentTable", back_populates="lesson_themes")
    exercises = relationship("ExerciseTable", back_populates="lesson_theme")
    view_data = relationship("ViewDataTable", back_populates="lesson_theme")
    answer_data = relationship("AnswerDataTable", back_populates="lesson_theme")
    questions = relationship("StudentQuestionTable", back_populates="lesson_theme")
    registrations = relationship("LessonRegistrationTable", back_populates="lesson_theme")
    # 🔽 新しいリレーション
    question_registrations = relationship("QuestionRegistrationTable", back_populates="lesson_theme")

    
# 10. 講義ビデオテーブル
class LectureVideosTable(Base):
    __tablename__ = "lecture_videos_table"
    lecture_video_id = Column(Integer, primary_key=True, autoincrement=True)
    lecture_video_title = Column(String(255))
    video_url = Column(String(255))
    lesson_theme = relationship("LessonThemesTable", back_populates="lecture_video")
    view_data = relationship("ViewDataTable", back_populates="lecture_video")

# 11. テキストテーブル
class TextbookTable(Base):
    __tablename__ = "textbooks_table"
    textbook_id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials_table.material_id"), nullable=False)
    textbook_name = Column(String(255))
    page_count = Column(Integer)
    image_url = Column(String(255))
    material = relationship("MaterialsTable", back_populates="textbooks")
    lesson_themes = relationship("LessonThemesTable", back_populates="textbook")

# 12. 資料テーブル
class DocumentTable(Base):
    __tablename__ = "documents_table"
    document_id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials_table.material_id"), nullable=False)
    document_name = Column(String(255))
    page_count = Column(Integer)
    document_url = Column(String(255))
    material = relationship("MaterialsTable", back_populates="documents")
    lesson_themes = relationship("LessonThemesTable", back_populates="document")

# 13. 問題テーブル
class QuestionTable(Base):
    __tablename__ = "questions_table"
    question_id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials_table.material_id"), nullable=False)
    question_type = Column(String(255))
    question_label = Column(String(255))
    question_text = Column(Text)  # ← ✅ ここを修正
    question_image_url = Column(String(255))
    material = relationship("MaterialsTable", back_populates="questions")
    choices = relationship("ChoiceTable", back_populates="question")
    answers = relationship("AnswerTable", back_populates="question")
    answer_data = relationship("AnswerDataTable", back_populates="question")  # 🔼 追加（任意）
    question_registrations = relationship("QuestionRegistrationTable", back_populates="question")



# 14. 選択肢テーブル
class ChoiceTable(Base):
    __tablename__ = "choices_table"
    choice_id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions_table.question_id"), nullable=False)
    choice_number = Column(Integer)
    choice_text = Column(String(255))
    answer_correctness = Column(Integer)
    choice_image_url = Column(String(255))
    question = relationship("QuestionTable", back_populates="choices")

# 15. 回答テーブル
class AnswerTable(Base):
    __tablename__ = "answers_table"
    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("questions_table.question_id"), nullable=False)

    answer_name = Column(String(255))
    answer_text = Column(Text)
    answer_image_url = Column(String(255))
    question = relationship("QuestionTable", back_populates="answers")

# 16. 演習テーブル
class ExerciseTable(Base):
    __tablename__ = "exercises_table"
    exercise_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=False)
    exercise_flag = Column(Boolean)
    exercise_time = Column(Integer)
    exercise_status = Column(String(10))
    lesson = relationship("LessonTable", back_populates="exercises")
    lesson_theme = relationship("LessonThemesTable", back_populates="exercises")

# 17. 視聴データテーブル
class ViewDataTable(Base):
    __tablename__ = "view_data_table"
    view_data_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=False)
    lecture_video_id = Column(Integer, ForeignKey("lecture_videos_table.lecture_video_id"), nullable=False)
    view_status = Column(Boolean)
    view_start_timestamp = Column(DateTime)
    total_view_time = Column(Float)
    student = relationship("StudentTable", back_populates="view_data")
    lesson = relationship("LessonTable", back_populates="view_data")
    lesson_theme = relationship("LessonThemesTable", back_populates="view_data")
    lecture_video = relationship("LectureVideosTable", back_populates="view_data")


# 18. 回答データテーブル
class AnswerDataTable(Base):
    __tablename__ = "answer_data_table"
    answer_data_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=True, default=None)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=True, default=None)
    question_id = Column(Integer, ForeignKey("questions_table.question_id"), nullable=False)

    # basic_question_number = Column(Integer, nullable=False)
    # advanced_question_number = Column(Integer, nullable=True)
    answer = Column(String(255))
    answer_correctness = Column(Boolean, nullable=True)
    answer_status = Column(Integer, nullable=True)
    answer_start_timestamp = Column(DateTime, nullable=True)
    answer_start_unix = Column(BigInteger, nullable=True)
    answer_end_timestamp = Column(DateTime, nullable=True)
    answer_end_unix = Column(BigInteger, nullable=True)
    student = relationship("StudentTable", back_populates="answer_data")
    lesson = relationship("LessonTable", back_populates="answer_data")
    lesson_theme = relationship("LessonThemesTable", back_populates="answer_data")
    question = relationship("QuestionTable", back_populates="answer_data") # 🔼 追加推奨


# 19. 質問テーブル
class StudentQuestionTable(Base):
    __tablename__ = "student_questions_table"
    student_question_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=False)
    question_text = Column(Text)
    question_datetime = Column(DateTime)
    checked = Column(Boolean)
    student = relationship("StudentTable", back_populates="questions")
    lesson = relationship("LessonTable", back_populates="questions")
    lesson_theme = relationship("LessonThemesTable", back_populates="questions")

# 20. 通知既読テーブル
class NotificationReadTable(Base):
    __tablename__ = "notification_reads_table"
    notification_read_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    notification_id = Column(Integer, ForeignKey("notifications_table.notification_id"), nullable=False)
    read_status = Column(Boolean)
    student = relationship("StudentTable", back_populates="notification_reads")
    notification = relationship("NotificationTable", back_populates="notification_reads")


# 21. 授業登録テーブル
class LessonRegistrationTable(Base):
    __tablename__ = "lesson_registrations_table"
    lesson_registration_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=False)
    lesson = relationship("LessonTable", back_populates="registrations")
    lesson_theme = relationship("LessonThemesTable", back_populates="registrations")

# 22. 問題登録テーブル
class QuestionRegistrationTable(Base):
    __tablename__ = "question_registrations_table"
    question_registration_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions_table.question_id"), nullable=False)

    lesson_theme = relationship("LessonThemesTable", back_populates="question_registrations")
    question = relationship("QuestionTable", back_populates="question_registrations")

