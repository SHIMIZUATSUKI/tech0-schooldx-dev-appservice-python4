from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from database import get_db
from models import AnswerDataTable, QuestionTable, ChoiceTable, AnswerTable, ExerciseTable
from schemas import AnswerDataWithDetails, QuestionDetail, Choice, Answer, LessonThemeDetail
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/answers", tags=["answer_data"])

@router.get("/", response_model=List[AnswerDataWithDetails])
def get_answer_data_with_details(
    student_id: int = Query(...),
    lesson_id: int = Query(...),
    db: Session = Depends(get_db)
):
    records = db.query(AnswerDataTable).options(
        joinedload(AnswerDataTable.question).joinedload(QuestionTable.choices),
        joinedload(AnswerDataTable.question).joinedload(QuestionTable.answers)
    ).filter(
        AnswerDataTable.student_id == student_id,
        AnswerDataTable.lesson_id == lesson_id
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="No matching answer data found.")

    result = []
    for row in records:
        question = row.question
        question_detail = QuestionDetail(
            question_id=question.question_id,
            question_type=question.question_type,
            question_label=question.question_label,
            question_text=question.question_text,
            question_image_url=question.question_image_url,
            choices=[
                Choice(
                    choice_id=c.choice_id,
                    choice_number=c.choice_number,
                    choice_text=c.choice_text,
                    answer_correctness=c.answer_correctness,
                    choice_image_url=c.choice_image_url
                ) for c in question.choices
            ],
            answers=[
                Answer(
                    answer_id=a.answer_id,
                    answer_name=a.answer_name,
                    answer_text=a.answer_text,
                    answer_image_url=a.answer_image_url
                ) for a in question.answers
            ]
        )

        # Exercise情報取得
        exercise = db.query(ExerciseTable).filter(
            ExerciseTable.lesson_id == row.lesson_id,
            ExerciseTable.lesson_theme_id == row.lesson_theme_id
        ).first()

        lesson_theme_detail = LessonThemeDetail(
            lesson_theme_id=row.lesson_theme_id or 0,
            exercise_flag=exercise.exercise_flag if exercise else False,
            exercise_status=exercise.exercise_status if exercise else ""
        ).dict()  # ← dictに変換して渡す

        result.append(AnswerDataWithDetails(
            answer_data_id=row.answer_data_id,
            student_id=row.student_id,
            lesson_id=row.lesson_id or 0,
            lesson_theme=lesson_theme_detail,  # ← dict形式で渡す
            question_id=row.question_id,
            answer=row.answer or "",
            answer_correctness=int(row.answer_correctness) if row.answer_correctness is not None else 0,
            answer_status=row.answer_status or 0,
            answer_start_timestamp=row.answer_start_timestamp or datetime.now(),
            answer_start_unix=row.answer_start_unix or 0,
            answer_end_timestamp=row.answer_end_timestamp or datetime.now(),
            answer_end_unix=row.answer_end_unix or 0,
            question=question_detail
        ))

    return result

# from fastapi import APIRouter, Depends, HTTPException, Query
# from sqlalchemy.orm import Session
# from database import get_db
# from models import AnswerDataTable
# from schemas import AnswerData
# from typing import List
# from datetime import datetime

# router = APIRouter(prefix="/api/answers", tags=["answer_data"])

# def to_safe_answer_data(row: AnswerDataTable) -> AnswerData:
#     return AnswerData(
#         answer_data_id=row.answer_data_id,
#         student_id=row.student_id,
#         lesson_id=row.lesson_id or 0,
#         lesson_theme_id=row.lesson_theme_id or 0,
#         question_id=row.question_id,
#         answer=row.answer or "",
#         answer_correctness=int(row.answer_correctness) if row.answer_correctness is not None else 0,
#         answer_status=row.answer_status or 0,
#         answer_start_timestamp=row.answer_start_timestamp or datetime.now(),
#         answer_start_unix=row.answer_start_unix or 0,
#         answer_end_timestamp=row.answer_end_timestamp or datetime.now(),
#         answer_end_unix=row.answer_end_unix or 0,
#     )

# @router.get("/", response_model=List[AnswerData])
# def get_filtered_answer_data(
#     student_id: int = Query(...),
#     lesson_id: int = Query(...),
#     db: Session = Depends(get_db)
# ):
#     data = db.query(AnswerDataTable).filter(
#         AnswerDataTable.student_id == student_id,
#         AnswerDataTable.lesson_id == lesson_id
#     ).all()

#     if not data:
#         raise HTTPException(status_code=404, detail="No matching answer data found.")

#     return [to_safe_answer_data(row) for row in data]

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from database import get_db
# from models import AnswerDataTable
# from schemas import AnswerData
# from typing import List
# from datetime import datetime

# router = APIRouter(prefix="/api/answers", tags=["answer_data"])

# def to_safe_answer_data(row: AnswerDataTable) -> AnswerData:
#     return AnswerData(
#         answer_data_id=row.answer_data_id,
#         student_id=row.student_id,
#         lesson_id=row.lesson_id or 0,
#         lesson_theme_id=row.lesson_theme_id or 0,
#         question_id=row.question_id,
#         answer=row.answer or "",
#         answer_correctness=int(row.answer_correctness) if row.answer_correctness is not None else 0,
#         answer_status=row.answer_status or 0,
#         answer_start_timestamp=row.answer_start_timestamp or datetime.now(),
#         answer_start_unix=row.answer_start_unix or 0,
#         answer_end_timestamp=row.answer_end_timestamp or datetime.now(),
#         answer_end_unix=row.answer_end_unix or 0,
#     )

# @router.get("/", response_model=List[AnswerData])
# def get_all_answer_data(db: Session = Depends(get_db)):
#     data = db.query(AnswerDataTable).all()
#     if not data:
#         raise HTTPException(status_code=404, detail="No answer data found.")
#     return [to_safe_answer_data(row) for row in data]