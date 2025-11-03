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

    # ▼▼▼▼▼ 【修正箇所】 ▼▼▼▼▼
    # JOINパスと Eager Loading を修正
    answer_data_list = (
        db.query(LessonAnswerDataTable)
        # 1. 生徒情報をJOIN (変更なし)
        .join(StudentTable, LessonAnswerDataTable.student_id == StudentTable.student_id)
        
        # 2. 問題情報をJOIN (変更なし)
        .join(LessonQuestionsTable, LessonAnswerDataTable.lesson_question_id == LessonQuestionsTable.lesson_question_id)
        
        # 3. テーマ情報 -> ユニット情報をJOIN (LAD.lesson_theme_id を使用)
        #    isouter=True (LEFT JOIN) にし、テーマやユニットがなくても回答データは取得できるようにする
        .join(LessonThemesTable, LessonAnswerDataTable.lesson_theme_id == LessonThemesTable.lesson_theme_id, isouter=True)
        .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id, isouter=True)
        
        .filter(LessonAnswerDataTable.lesson_id == lesson_id)
        
        # Eager Loading (リレーションシップに合わせて修正)
        .options(
            joinedload(LessonAnswerDataTable.student),
            joinedload(LessonAnswerDataTable.lesson_question),
            joinedload(LessonAnswerDataTable.lesson_theme).joinedload(LessonThemesTable.unit)
        )
        .all()
    )
    # ▲▲▲▲▲ 【修正箇所】 ▲▲▲▲▲
    
    if not answer_data_list:
        return []

    result = []
    for ad in answer_data_list:
        # ▼▼▼▼▼ 【修正箇所】 ▼▼▼▼▼
        # ad (LessonAnswerDataTable) から直接リレーションをたどる
        student = ad.student
        question = ad.lesson_question
        theme = ad.lesson_theme  # ad.lesson_theme を使う
        unit = theme.unit if theme else None

        # 回答データ(ad)、生徒(student)、問題(question) があれば最低限処理する
        # (theme や unit は null でも可)
        if not student or not question:
            continue
        
        choice_labels = {1: "A", 2: "B", 3: "C", 4: "D"}
        selected_choice = choice_labels.get(ad.choice_number)
        
        correct_choice_num = question.correctness_number
        correct_choice = choice_labels.get(correct_choice_num) if correct_choice_num is not None else None

        is_correct_val = None # 初期値は None
        if ad.answer_correctness is not None:
             is_correct_val = ad.answer_correctness
        elif selected_choice is not None and correct_choice is not None:
             is_correct_val = (selected_choice == correct_choice)

        result.append(GradesRawDataItem(
            student=StudentInfo(
                student_id=student.student_id,
                name=student.name,
                class_id=student.class_id
            ),
            question=QuestionInfo(
                question_id=question.lesson_question_id,
                question_label=question.lesson_question_label or f"問{question.lesson_question_id}",
                correct_choice=correct_choice or "B", # フロントエンドのロジック(80行目)に合わせる
                part_name=unit.part_name if unit else None,
                chapter_name=unit.chapter_name if unit else None,
                unit_name=unit.unit_name if unit else None,
                lesson_theme_name=theme.lesson_theme_name if theme else None
            ),
            answer=AnswerInfo(
                selected_choice=selected_choice,
                is_correct=is_correct_val,
                start_unix=ad.answer_start_unix,
                end_unix=ad.answer_end_unix
            )
        ))
        # ▲▲▲▲▲ 【修正箇所】 ▲▲▲▲▲
    
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