from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Date, DateTime, Text, Float, BigInteger
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class ClassTable(Base):
    __tablename__ = "class_table"
    
    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(255))
    grade = Column(Integer)
    teacher = Column(String(255))
    academic_year = Column(Integer)
    
    students = relationship("StudentTable", back_populates="class_ref")
    lessons = relationship("LessonTable", back_populates="class_ref")

class StudentTable(Base):
    __tablename__ = "students_table"
    
    student_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("class_table.class_id"), nullable=False)
    students_number = Column(Integer, nullable=False)
    name = Column(String(255))
    mail_address = Column(String(255), unique=True)
    password = Column(String(255))
    enrollment_year = Column(Integer)
    
    class_ref = relationship("ClassTable", back_populates="students")
    lesson_answer_data = relationship("LessonAnswerDataTable", back_populates="student")
    lesson_surveys = relationship("LessonSurveyTable", back_populates="student")

class StatusTable(Base):
    __tablename__ = "status_table"
    
    status_id = Column(Integer, primary_key=True, autoincrement=True)
    status_name = Column(String(255))

class TimetableTable(Base):
    __tablename__ = "timetable_table"
    
    timetable_id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    day_of_week = Column(String(10))
    period = Column(Integer)
    time = Column(String(11))
    
    lessons = relationship("LessonTable", back_populates="timetable")

class LessonTable(Base):
    __tablename__ = "lessons_table"
    
    lesson_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("class_table.class_id"), nullable=False)
    timetable_id = Column(Integer, ForeignKey("timetable_table.timetable_id"), nullable=False)
    lesson_name = Column(String(255))
    lesson_status = Column(Integer, ForeignKey("status_table.status_id"), nullable=False)
    
    class_ref = relationship("ClassTable", back_populates="lessons")
    timetable = relationship("TimetableTable", back_populates="lessons")
    status = relationship("StatusTable")
    registrations = relationship("LessonRegistrationTable", back_populates="lesson")
    lesson_answer_data = relationship("LessonAnswerDataTable", back_populates="lesson")

class MaterialTable(Base):
    __tablename__ = "materials_table"
    
    material_id = Column(Integer, primary_key=True, autoincrement=True)
    material_name = Column(String(255))
    
    units = relationship("UnitTable", back_populates="material")

class UnitTable(Base):
    __tablename__ = "units_table"
    
    units_id = Column(Integer, primary_key=True, autoincrement=True)
    material_id = Column(Integer, ForeignKey("materials_table.material_id"), nullable=False)
    part_name = Column(String(255))
    chapter_name = Column(String(255))
    unit_name = Column(String(255))
    
    material = relationship("MaterialTable", back_populates="units")
    lesson_themes = relationship("LessonThemesTable", back_populates="unit")

class LessonThemeContentsTable(Base):
    __tablename__ = "lesson_theme_contents_table"
    
    lesson_theme_contents_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_question_status = Column(Integer, ForeignKey("status_table.status_id"), nullable=False)
    lesson_survey_id = Column(Integer, ForeignKey("lesson_survey_table.lesson_survey_id"), nullable=False)
    
    status = relationship("StatusTable")
    lesson_survey = relationship("LessonSurveyTable")
    lesson_questions = relationship("LessonQuestionsTable", back_populates="lesson_theme_contents")
    lesson_themes = relationship("LessonThemesTable", back_populates="lesson_theme_contents")

class LessonThemesTable(Base):
    __tablename__ = "lesson_themes_table"
    
    lesson_theme_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_theme_contents_id = Column(Integer, ForeignKey("lesson_theme_contents_table.lesson_theme_contents_id"), nullable=False)
    units_id = Column(Integer, ForeignKey("units_table.units_id"), nullable=False)
    lesson_theme_name = Column(String(255))
    
    lesson_theme_contents = relationship("LessonThemeContentsTable", back_populates="lesson_themes")
    unit = relationship("UnitTable", back_populates="lesson_themes")
    registrations = relationship("LessonRegistrationTable", back_populates="lesson_theme")
    lesson_answer_data = relationship("LessonAnswerDataTable", back_populates="lesson_theme")
    lesson_surveys = relationship("LessonSurveyTable", back_populates="lesson_theme")

class LessonRegistrationTable(Base):
    __tablename__ = "lesson_registrations_table"
    
    lesson_registration_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=False)
    
    lesson = relationship("LessonTable", back_populates="registrations")
    lesson_theme = relationship("LessonThemesTable", back_populates="registrations")

class LessonQuestionsTable(Base):
    __tablename__ = "lesson_questions_table"
    
    lesson_question_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_theme_contents_id = Column(Integer, ForeignKey("lesson_theme_contents_table.lesson_theme_contents_id"), nullable=False)
    lesson_question_label = Column(String(255))
    question_text1 = Column(Text)
    question_text2 = Column(Text)
    question_text3 = Column(Text)
    question_text4 = Column(Text)
    correctness_number = Column(Integer)
    
    lesson_theme_contents = relationship("LessonThemeContentsTable", back_populates="lesson_questions")
    lesson_answer_data = relationship("LessonAnswerDataTable", back_populates="lesson_question")

class LessonAnswerDataTable(Base):
    __tablename__ = "lesson_answer_data_table"
    
    lesson_answer_data_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"))
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"))
    lesson_question_id = Column(Integer, ForeignKey("lesson_questions_table.lesson_question_id"), nullable=False)
    choice_number = Column(Integer)
    answer_correctness = Column(Boolean)
    answer_status = Column(Integer, ForeignKey("status_table.status_id"), nullable=False)
    answer_start_timestamp = Column(DateTime)
    answer_start_unix = Column(BigInteger)
    answer_end_timestamp = Column(DateTime)
    answer_end_unix = Column(BigInteger)
    
    student = relationship("StudentTable", back_populates="lesson_answer_data")
    lesson = relationship("LessonTable", back_populates="lesson_answer_data")
    lesson_theme = relationship("LessonThemesTable", back_populates="lesson_answer_data")
    lesson_question = relationship("LessonQuestionsTable", back_populates="lesson_answer_data")
    status = relationship("StatusTable")

class LessonSurveyTable(Base):
    __tablename__ = "lesson_survey_table"
    
    lesson_survey_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=True, default=None)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"))
    survey_status = Column(Integer, ForeignKey("status_table.status_id"), nullable=False)
    understanding_level = Column(Integer)
    difficulty_point = Column(Integer)
    student_comment = Column(String(255))
    
    student = relationship("StudentTable", back_populates="lesson_surveys")
    lesson = relationship("LessonTable", back_populates="surveys")
    lesson_theme = relationship("LessonThemesTable", back_populates="lesson_surveys")
    status = relationship("StatusTable")

class LectureVideosTable(Base):
    __tablename__ = "lecture_videos_table"
    
    lecture_video_id = Column(Integer, primary_key=True, autoincrement=True)
    lesson_theme_id = Column(Integer, ForeignKey("lesson_themes_table.lesson_theme_id"), nullable=False)
    lecture_video_title = Column(String(255))
    video_url = Column(String(255))
    
    lesson_theme = relationship("LessonThemesTable")

class AttendanceTable(Base):
    __tablename__ = "attendance_table"
    
    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
    lesson_id = Column(Integer, ForeignKey("lessons_table.lesson_id"), nullable=False)
    attendance_status = Column(Boolean, default=False)
    
    student = relationship("StudentTable")
    lesson = relationship("LessonTable")



# 以下、存在しないテーブルを一度コメントアウト 

# class AnswerDataTable(Base):
#     __tablename__ = "answer_data_table"
    
#     answer_data_id = Column(Integer, primary_key=True, autoincrement=True)
#     student_id = Column(Integer, ForeignKey("students_table.student_id"), nullable=False)
#     lesson_id = Column(Integer)
#     lesson_theme_id = Column(Integer)
#     question_id = Column(Integer)
#     answer = Column(String(255))
#     answer_correctness = Column(Boolean)
#     answer_status = Column(Integer)
#     answer_start_timestamp = Column(DateTime)
#     answer_start_unix = Column(BigInteger)
#     answer_end_timestamp = Column(DateTime)
#     answer_end_unix = Column(BigInteger)

# class QuestionTable(Base):
#     __tablename__ = "questions_table"
    
#     question_id = Column(Integer, primary_key=True, autoincrement=True)
#     question_type = Column(String(50))
#     question_label = Column(String(255))
#     question_text = Column(Text)
#     question_image_url = Column(String(255))
    
#     choices = relationship("ChoiceTable", back_populates="question")
#     answers = relationship("AnswerTable", back_populates="question")

# class ChoiceTable(Base):
#     __tablename__ = "choices_table"
    
#     choice_id = Column(Integer, primary_key=True, autoincrement=True)
#     question_id = Column(Integer, ForeignKey("questions_table.question_id"), nullable=False)
#     choice_number = Column(Integer)
#     choice_text = Column(String(255))
#     answer_correctness = Column(Integer)
#     choice_image_url = Column(String(255))
    
#     question = relationship("QuestionTable", back_populates="choices")

# class AnswerTable(Base):
#     __tablename__ = "answers_table"
    
#     answer_id = Column(Integer, primary_key=True, autoincrement=True)
#     question_id = Column(Integer, ForeignKey("questions_table.question_id"), nullable=False)
#     answer_name = Column(String(255))
#     answer_text = Column(Text)
#     answer_image_url = Column(String(255))
    
#     question = relationship("QuestionTable", back_populates="answers")

# class ExerciseTable(Base):
#     __tablename__ = "exercises_table"
    
#     exercise_id = Column(Integer, primary_key=True, autoincrement=True)
#     lesson_id = Column(Integer)
#     lesson_theme_id = Column(Integer)
#     exercise_flag = Column(Boolean)
#     exercise_time = Column(Integer)
#     exercise_status = Column(String(10))