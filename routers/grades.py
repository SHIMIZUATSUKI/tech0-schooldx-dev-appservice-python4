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

    try:
        answer_data_list = (
            db.query(LessonAnswerDataTable)
            # 1. 生徒情報をJOIN
            .join(StudentTable, LessonAnswerDataTable.student_id == StudentTable.student_id)
            
            # 2. 問題情報をJOIN
            .join(LessonQuestionsTable, LessonAnswerDataTable.lesson_question_id == LessonQuestionsTable.lesson_question_id)
            
            # 3. テーマ情報 -> ユニット情報をJOIN (LAD.lesson_theme_id を使用)
            .join(LessonThemesTable, LessonAnswerDataTable.lesson_theme_id == LessonThemesTable.lesson_theme_id, isouter=True)
            .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id, isouter=True)
            
            .filter(LessonAnswerDataTable.lesson_id == lesson_id)
            
            # Eager Loading
            .options(
                joinedload(LessonAnswerDataTable.student),
                joinedload(LessonAnswerDataTable.lesson_question),
                joinedload(LessonAnswerDataTable.lesson_theme).joinedload(LessonThemesTable.unit)
            )
            .all()
        )
    
    except Exception as e:
        # DBクエリ自体が失敗した場合（デバッグ用）
        print(f"!!! /grades/raw_data DBクエリ エラー: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {e}")

    if not answer_data_list:
        return []

    result = []
    try:
        for ad in answer_data_list:
            student = ad.student
            question = ad.lesson_question
            theme = ad.lesson_theme
            unit = theme.unit if theme else None

            if not student or not question:
                continue
            
            choice_labels = {1: "A", 2: "B", 3: "C", 4: "D"}
            selected_choice = choice_labels.get(ad.choice_number)
            
            correct_choice_num = question.correctness_number
            correct_choice = choice_labels.get(correct_choice_num) if correct_choice_num is not None else None

            is_correct_val = None
            if ad.answer_correctness is not None:
                is_correct_val = ad.answer_correctness
            elif selected_choice is not None and correct_choice is not None:
                is_correct_val = (selected_choice == correct_choice)

            # ▼▼▼▼▼ 【500エラー対策】 student.name が None の場合に対応 ▼▼▼▼▼
            student_name = student.name or "名前なし" 
            # ▲▲▲▲▲ 【500エラー対策】 ▲▲▲▲▲

            result.append(GradesRawDataItem(
                student=StudentInfo(
                    student_id=student.student_id,
                    name=student_name, # 修正
                    class_id=student.class_id
                ),
                question=QuestionInfo(
                    question_id=question.lesson_question_id,
                    question_label=question.lesson_question_label or f"問{question.lesson_question_id}",
                    correct_choice=correct_choice or "B", 
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
            
    except Exception as e:
        # ループ内でのデータ変換エラー（デバッグ用）
        print(f"!!! /grades/raw_data データ処理ループ エラー: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Data processing error: {e}")
    
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

    # ▼▼▼▼▼ 【Comments絞り込み修正】 ▼▼▼▼▼
    
    # 1. この授業のクラスID (target_class_id) を取得
    target_class_id = lesson.class_id
    
    # 2. そのクラスに所属する生徒のID一覧 (Set) を取得
    student_ids_in_class = db.query(StudentTable.student_id).filter(
        StudentTable.class_id == target_class_id
    ).all()
    
    target_student_id_set = {s_id for (s_id,) in student_ids_in_class}

    if not target_student_id_set:
        return GradesCommentsResponse(lesson_id=lesson_id, comments=[])

    # ▲▲▲▲▲ 【Comments絞り込み修正】 ▲▲▲▲▲
    
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
            # ▼▼▼▼▼ 【Comments絞り込み修正】 ▼▼▼▼▼
            # 3. アンケートの student_id が、対象クラスの生徒ID (Set) に含まれているかチェック
            if survey.student_comment and survey.student_id in target_student_id_set:
            # ▲▲▲▲▲ 【Comments絞り込み修正】 ▲▲▲▲▲
                
                student = db.query(StudentTable).filter(
                    StudentTable.student_id == survey.student_id
                ).first()
                
                if student:
                    comments.append(StudentComment(
                        student_id=student.student_id,
                        student_name=student.name, # student.name は NULL可だが、CommentスキーマはOK
                        comment_text=survey.student_comment
                    ))
    
    return GradesCommentsResponse(
        lesson_id=lesson_id,
        comments=comments
    )