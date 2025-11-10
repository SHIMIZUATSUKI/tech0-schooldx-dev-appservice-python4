# routers/grades.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from typing import List
import traceback # エラー詳細出力のためインポート
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
    
    try:
        lesson = db.query(LessonTable).filter(LessonTable.lesson_id == lesson_id).first()
        if not lesson:
            raise HTTPException(status_code=404, detail="Lesson not found")

        answer_data_list = (
            db.query(LessonAnswerDataTable)
            .join(StudentTable, LessonAnswerDataTable.student_id == StudentTable.student_id)
            .join(LessonQuestionsTable, LessonAnswerDataTable.lesson_question_id == LessonQuestionsTable.lesson_question_id)
            .join(LessonThemesTable, LessonAnswerDataTable.lesson_theme_id == LessonThemesTable.lesson_theme_id, isouter=True)
            .join(UnitTable, LessonThemesTable.units_id == UnitTable.units_id, isouter=True)
            .filter(LessonAnswerDataTable.lesson_id == lesson_id)
            .options(
                joinedload(LessonAnswerDataTable.student),
                joinedload(LessonAnswerDataTable.lesson_question),
                joinedload(LessonAnswerDataTable.lesson_theme).joinedload(LessonThemesTable.unit)
            )
            .all()
        )

        if not answer_data_list:
            return []

        result = []
        
        for i, ad in enumerate(answer_data_list):
            
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
            
            student_name = student.name or "名前なし" 

            result.append(GradesRawDataItem(
                student=StudentInfo(
                    student_id=student.student_id,
                    name=student_name,
                    class_id=student.class_id,
                    # ▼▼▼▼▼ 【修正】エラーログに基づき、不足していた students_number を追加 ▼▼▼▼▼
                    students_number=student.students_number
                    # ▲▲▲▲▲ 【修正】 ▲▲▲▲▲
                ),
                question=QuestionInfo(
                    question_id=question.lesson_question_id,
                    question_label=question.lesson_question_label or f"問{question.lesson_question_id}",
                    correct_choice=correct_choice or "B", 
                    part_name=unit.part_name if unit else None,
                    chapter_name=unit.chapter_name if unit else None,
                    unit_name=unit.unit_name if unit else None,
                    lesson_theme_name=theme.lesson_theme_name if theme else None,
                    lesson_theme_contents_id=question.lesson_theme_contents_id
                ),
                answer=AnswerInfo(
                    selected_choice=selected_choice,
                    is_correct=is_correct_val,
                    start_unix=ad.answer_start_unix,
                    end_unix=ad.answer_end_unix
                )
            ))
        
        return result

    except Exception as e:
        print(f"!!! /grades/raw_data エラー発生 !!!: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")


@router.get("/comments", response_model=GradesCommentsResponse)
def get_grades_comments(
    lesson_id: int = Query(..., description="授業ID（必須）"),
    db: Session = Depends(get_db)
):
    """
    指定した授業の全生徒のアンケートコメントを取得する。
    定性分析に使用する。
    """
    try:
        # LessonSurveyTable から lesson_id で直接絞り込み、StudentTable と結合して生徒名を取得
        surveys = (
            db.query(
                LessonSurveyTable.student_id,
                StudentTable.name,
                LessonSurveyTable.student_comment
            )
            .join(StudentTable, LessonSurveyTable.student_id == StudentTable.student_id)
            .filter(LessonSurveyTable.lesson_id == lesson_id)
            .filter(LessonSurveyTable.student_comment.isnot(None)) # コメントがNULLでないもの
            .filter(LessonSurveyTable.student_comment != '')      # コメントが空文字列でないもの
            .all()
        )

        # 取得した結果をPydanticモデルに変換
        comments = [
            StudentComment(
                student_id=student_id,
                student_name=student_name,
                comment_text=comment_text
            )
            for student_id, student_name, comment_text in surveys
        ]

        return GradesCommentsResponse(
            lesson_id=lesson_id,
            comments=comments
        )

    except Exception as e:
        print(f"!!! /grades/comments エラー発生 !!!: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")