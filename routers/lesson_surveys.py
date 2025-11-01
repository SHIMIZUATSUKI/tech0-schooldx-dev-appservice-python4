# routers/lesson_surveys.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models import LessonSurveyTable, StudentTable, LessonTable, LessonThemesTable
from schemas import LessonSurveyCreate, LessonSurveyResponse
from typing import List, Optional

router = APIRouter(
    prefix="/lesson_surveys",
    tags=["lesson_surveys"]
)

@router.post("/", response_model=LessonSurveyResponse, status_code=status.HTTP_201_CREATED)
def create_lesson_survey(
    student_id: int = Query(...),
    lesson_id: Optional[int] = Query(None),
    lesson_theme_id: Optional[int] = Query(None),
    understanding_level: Optional[int] = Query(None),
    difficulty_point: Optional[int] = Query(None),
    student_comment: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    授業アンケート（学生コメント）を登録するエンドポイント

    クエリパラメータ:
    - student_id (int, 必須): 学生ID
    - lesson_id (Optional[int]): 授業ID
    - lesson_theme_id (Optional[int]): 授業テーマID
    - understanding_level (Optional[int]): 理解度レベル（1-5 など）
    - difficulty_point (Optional[int]): 難易度ポイント（1-5 など）
    - student_comment (Optional[str]): 学生のコメント

    使用例:
    POST /lesson_surveys/?student_id=1&lesson_theme_id=5&understanding_level=4&difficulty_point=2&student_comment=大変良く理解できた
    """
    try:
        # 学生の存在確認
        student = db.query(StudentTable).filter(
            StudentTable.student_id == student_id
        ).first()

        if not student:
            raise HTTPException(
                status_code=404,
                detail=f"学生ID {student_id} が見つかりません"
            )

        # lesson_id が指定されている場合、授業の存在確認
        if lesson_id:
            lesson = db.query(LessonTable).filter(
                LessonTable.lesson_id == lesson_id
            ).first()

            if not lesson:
                raise HTTPException(
                    status_code=404,
                    detail=f"授業ID {lesson_id} が見つかりません"
                )

        # lesson_theme_id が指定されている場合、授業テーマの存在確認
        if lesson_theme_id:
            lesson_theme = db.query(LessonThemesTable).filter(
                LessonThemesTable.lesson_theme_id == lesson_theme_id
            ).first()

            if not lesson_theme:
                raise HTTPException(
                    status_code=404,
                    detail=f"授業テーマID {lesson_theme_id} が見つかりません"
                )

        # 新しいアンケートレコードを作成
        new_survey = LessonSurveyTable(
            student_id=student_id,
            lesson_theme_id=lesson_theme_id,
            survey_status=1,  # デフォルトステータス（提出済み）
            understanding_level=understanding_level,
            difficulty_point=difficulty_point,
            student_comment=student_comment
        )

        db.add(new_survey)
        db.commit()
        db.refresh(new_survey)

        return LessonSurveyResponse.from_orm(new_survey)

    except HTTPException:
        raise
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="データベースの制約エラーが発生しました"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"内部エラーが発生しました: {str(e)}"
        )

@router.get("/", response_model=List[LessonSurveyResponse])
def get_lesson_surveys(
    student_id: Optional[int] = Query(None),
    lesson_theme_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    """
    学生のアンケート履歴を取得するエンドポイント

    クエリパラメータ:
    - student_id (Optional[int]): 学生IDでフィルター
    - lesson_theme_id (Optional[int]): 授業テーマIDでフィルター
    """
    try:
        query = db.query(LessonSurveyTable)

        if student_id:
            query = query.filter(LessonSurveyTable.student_id == student_id)

        if lesson_theme_id:
            query = query.filter(LessonSurveyTable.lesson_theme_id == lesson_theme_id)

        surveys = query.all()
        return [LessonSurveyResponse.from_orm(survey) for survey in surveys]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"内部エラーが発生しました: {str(e)}"
        )

@router.get("/{survey_id}", response_model=LessonSurveyResponse)
def get_lesson_survey_by_id(
    survey_id: int,
    db: Session = Depends(get_db)
):
    """
    特定のアンケートレコードを取得するエンドポイント

    パスパラメータ:
    - survey_id (int): アンケートID
    """
    try:
        survey = db.query(LessonSurveyTable).filter(
            LessonSurveyTable.lesson_survey_id == survey_id
        ).first()

        if not survey:
            raise HTTPException(
                status_code=404,
                detail=f"アンケートID {survey_id} が見つかりません"
            )

        return LessonSurveyResponse.from_orm(survey)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"内部エラーが発生しました: {str(e)}"
        )

@router.put("/{survey_id}", response_model=LessonSurveyResponse)
def update_lesson_survey(
    survey_id: int,
    understanding_level: Optional[int] = Query(None),
    difficulty_point: Optional[int] = Query(None),
    student_comment: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    既存のアンケートレコードを更新するエンドポイント

    パスパラメータ:
    - survey_id (int): 更新対象のアンケートID

    クエリパラメータ:
    - understanding_level (Optional[int]): 理解度レベル（1-5 など）
    - difficulty_point (Optional[int]): 難易度ポイント（1-5 など）
    - student_comment (Optional[str]): 学生のコメント
    """
    try:
        survey = db.query(LessonSurveyTable).filter(
            LessonSurveyTable.lesson_survey_id == survey_id
        ).first()

        if not survey:
            raise HTTPException(
                status_code=404,
                detail=f"アンケートID {survey_id} が見つかりません"
            )

        # フィールドを更新
        if understanding_level is not None:
            survey.understanding_level = understanding_level

        if difficulty_point is not None:
            survey.difficulty_point = difficulty_point

        if student_comment is not None:
            survey.student_comment = student_comment

        db.commit()
        db.refresh(survey)

        return LessonSurveyResponse.from_orm(survey)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"内部エラーが発生しました: {str(e)}"
        )

@router.delete("/{survey_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lesson_survey(
    survey_id: int,
    db: Session = Depends(get_db)
):
    """
    アンケートレコードを削除するエンドポイント

    パスパラメータ:
    - survey_id (int): 削除対象のアンケートID
    """
    try:
        survey = db.query(LessonSurveyTable).filter(
            LessonSurveyTable.lesson_survey_id == survey_id
        ).first()

        if not survey:
            raise HTTPException(
                status_code=404,
                detail=f"アンケートID {survey_id} が見つかりません"
            )

        db.delete(survey)
        db.commit()

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"内部エラーが発生しました: {str(e)}"
        )
