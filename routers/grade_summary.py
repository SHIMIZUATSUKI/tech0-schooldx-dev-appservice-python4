# routers/grade_summary.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from pydantic import BaseModel
from typing import List
from database import get_db
from models import (
    LessonAnswerDataTable,
    LessonQuestionsTable,
    StudentTable,
    ClassTable
)

router = APIRouter(prefix="/grades", tags=["grades"])

# レスポンスの型定義
class GradeQuestionSummary(BaseModel):
    question_id: int
    question_label: str
    total_answers: int
    correct_answers: int
    correct_rate: float

class GradeSummaryResponse(BaseModel):
    academic_year: int
    grade: int
    summary: List[GradeQuestionSummary]

@router.get("/grade_summary", response_model=GradeSummaryResponse)
def get_grade_summary(
    academic_year: int = Query(..., description="年度 (例: 2025)"),
    grade: int = Query(..., description="学年 (例: 1)"),
    db: Session = Depends(get_db)
):
    """
    指定された年度・学年全体の設問別正答率を集計して返す。
    """
    # `academic_year` と `grade` の両方でクラスを絞り込み
    class_ids = db.query(ClassTable.class_id).filter(
        ClassTable.academic_year == academic_year,
        ClassTable.grade == grade
    ).all()
    
    if not class_ids:
        raise HTTPException(status_code=404, detail="指定された学年のクラスが見つかりません。")
    
    target_class_ids = [c_id for (c_id,) in class_ids]

    student_ids = db.query(StudentTable.student_id).filter(
        StudentTable.class_id.in_(target_class_ids)
    ).all()

    if not student_ids:
        raise HTTPException(status_code=404, detail="指定された学年の生徒が見つかりません。")

    target_student_ids = [s_id for (s_id,) in student_ids]

    query_result = (
        db.query(
            LessonAnswerDataTable.lesson_question_id,
            LessonQuestionsTable.lesson_question_label,
            func.count(LessonAnswerDataTable.lesson_answer_data_id).label("total_answers"),
            func.sum(
                case(
                    (LessonAnswerDataTable.choice_number == LessonQuestionsTable.correctness_number, 1),
                    else_=0
                )
            ).label("correct_answers")
        )
        .join(LessonQuestionsTable, LessonAnswerDataTable.lesson_question_id == LessonQuestionsTable.lesson_question_id)
        .filter(
            LessonAnswerDataTable.student_id.in_(target_student_ids),
            LessonAnswerDataTable.choice_number.isnot(None) # 未回答のデータは集計から除外
        )
        .group_by(
            LessonAnswerDataTable.lesson_question_id,
            LessonQuestionsTable.lesson_question_label
        )
        .all()
    )

    summary_list = []
    for row in query_result:
        question_id = row.lesson_question_id
        question_label = row.lesson_question_label
        total_answers = row.total_answers
        correct_answers = row.correct_answers or 0
        
        correct_rate = (correct_answers / total_answers) * 100 if total_answers > 0 else 0
        summary_list.append(GradeQuestionSummary(
            question_id=question_id,
            question_label=question_label,
            total_answers=total_answers,
            correct_answers=correct_answers,
            correct_rate=round(correct_rate, 1)
        ))
            
    return GradeSummaryResponse(
        academic_year=academic_year,
        grade=grade,
        summary=summary_list
    )