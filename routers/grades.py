# routers/grades.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import get_db
from models import (
    LessonAnswerDataTable, LessonQuestionsTable, StudentTable, LessonTable,
    LessonThemesTable, LessonSurveyTable, LessonRegistrationTable,
    LessonThemeContentsTable, UnitTable
)
from schemas import GradesRawDataItem, GradesCommentsResponse, StudentComment, StudentInfo, QuestionInfo, AnswerInfo

router = APIRouter(prefix="/grades", tags=["grades"])

@router.get("/raw_data", response_model=List[GradesRawDataItem])
def get_grades_raw_data(
    lesson_id: int = Query(..., description="授業ID（必須）"),
    db: Session = Depends(get_db)
):
    lesson = db.query(LessonTable).filter(LessonTable.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")

    answer_data_list = (
        db.query(LessonAnswerDataTable)
        .join(StudentTable, LessonAnswerDataTable.student_id == StudentTable.student_id)
        .join(LessonQuestionsTable, LessonAnswerDataTable.lesson_question_id == LessonQuestionsTable.lesson_question_id)
        .join(LessonThemeContentsTable, LessonQuestionsTable.lesson_theme_contents_id == LessonThemeContentsTable.lesson_theme_contents_id)
        .join(LessonThemesTable, LessonThemeContentsTable.lesson_theme_contents_id == LessonThemesTable.lesson_theme_contents_id)
        .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id)
        .filter(LessonAnswerDataTable.lesson_id == lesson_id)
        .options(
            joinedload(LessonAnswerDataTable.student),
            joinedload(LessonAnswerDataTable.lesson_question).joinedload(LessonQuestionsTable.lesson_theme_contents).joinedload(LessonThemeContentsTable.lesson_themes).joinedload(LessonThemesTable.unit)
        )
        .all()
    )
    
    if not answer_data_list:
        return []

    result = []
    for ad in answer_data_list:
        student = ad.student
        question = ad.lesson_question
        theme = question.lesson_theme_contents.lesson_themes[0] if question.lesson_theme_contents.lesson_themes else None
        unit = theme.unit if theme else None

        if not student or not question or not unit or not theme:
            continue
            
        choice_labels = {1: "A", 2: "B", 3: "C", 4: "D"}
        selected_choice = choice_labels.get(ad.choice_number)
        correct_choice = choice_labels.get(question.correctness_number)

        is_correct_val = False
        if selected_choice is not None and correct_choice is not None:
            is_correct_val = (selected_choice == correct_choice)

        result.append(GradesRawDataItem(
            student=StudentInfo(
                student_id=student.student_id,
                name=student.name,
                class_id=student.class_id,
                students_number=student.students_number
            ),
            question=QuestionInfo(
                question_id=question.lesson_question_id,
                question_label=question.lesson_question_label or f"問{question.lesson_question_id}",
                correct_choice=correct_choice or "B",
                part_name=unit.part_name,
                chapter_name=unit.chapter_name,
                unit_name=unit.unit_name,
                lesson_theme_name=theme.lesson_theme_name
            ),
            answer=AnswerInfo(
                selected_choice=selected_choice,
                is_correct=is_correct_val,
                start_unix=ad.answer_start_unix,
                end_unix=ad.answer_end_unix
            )
        ))
    
    return result

@router.get("/comments", response_model=GradesCommentsResponse)
def get_grades_comments(
    lesson_id: int = Query(..., description="授業ID（必須）"),
    db: Session = Depends(get_db)
):
    """
    指定した授業の全生徒のアンケートコメントを取得する。
    定性分析に使用する。
    """
    lesson = db.query(LessonTable).filter(LessonTable.lesson_id == lesson_id).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found")
    
    lesson_registrations = (
        db.query(LessonRegistrationTable)
        .filter(LessonRegistrationTable.lesson_id == lesson_id)
        .all()
    )
    
    if not lesson_registrations:
        return GradesCommentsResponse(lesson_id=lesson_id, comments=[])
    
    comments = []
    for registration in lesson_registrations:
        surveys = (
            db.query(LessonSurveyTable)
            .filter(LessonSurveyTable.lesson_theme_id == registration.lesson_theme_id)
            .all()
        )
        
        for survey in surveys:
            if survey.student_comment:
                student = db.query(StudentTable).filter(
                    StudentTable.student_id == survey.student_id
                ).first()
                
                if student:
                    comments.append(StudentComment(
                        student_id=student.student_id,
                        student_name=student.name,
                        comment_text=survey.student_comment
                    ))
    
    return GradesCommentsResponse(
        lesson_id=lesson_id,
        comments=comments
    )