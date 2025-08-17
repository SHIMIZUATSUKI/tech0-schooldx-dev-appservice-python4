####### lecture_videos.py

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import LectureVideosTable, LessonThemesTable
from schemas import LectureVideo
from services.azure_blob import upload_file_to_blob, delete_file_from_blob

router = APIRouter(prefix="/lecture_videos", tags=["lecture_videos"])


@router.post("/", response_model=LectureVideo)
def create_lecture_video(
    lesson_theme_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    1テーマ1動画の運用を想定。
    - すでに同じ lesson_theme_id で動画があればエラー(400)
    - 利用者は先に DELETE で既存動画を削除し、新規登録を行う流れ
    """
    # 既に登録済みかどうかを確認
    existing_video = db.query(LectureVideosTable).filter(
        LectureVideosTable.lesson_theme_id == lesson_theme_id
    ).first()
    if existing_video:
        raise HTTPException(
            status_code=400,
            detail=f"Video already registered for lesson_theme_id={lesson_theme_id}. "
                "Please delete it before creating a new one."
        )

    # lesson_theme_id が実在するか確認 (任意)
    lesson_theme = db.query(LessonThemesTable).filter(
        LessonThemesTable.lesson_theme_id == lesson_theme_id
    ).first()
    if not lesson_theme:
        raise HTTPException(status_code=404, detail="Lesson theme not found")

    # Blob へアップロード
    file_data = file.file.read()
    blob_url = upload_file_to_blob(file_data, file.filename)

    # DB 登録
    new_video = LectureVideosTable(
        lesson_theme_id=lesson_theme_id,
        lecture_video_title=lesson_theme.lesson_theme_name,  # タイトルはテーマ名を流用する例
        video_url=blob_url
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    return new_video


@router.get("/", response_model=List[LectureVideo])
def list_lecture_videos(
    lesson_theme_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    指定された theme_id の動画をリストで返す。
    1テーマ1動画運用でも、リスト形式で返して問題ありません。
    """
    query = db.query(LectureVideosTable)
    if lesson_theme_id is not None:
        query = query.filter(LectureVideosTable.lesson_theme_id == lesson_theme_id)
    return query.all()


@router.delete("/{lecture_video_id}")
def delete_lecture_video(
    lecture_video_id: int,
    db: Session = Depends(get_db)
):
    """
    - 指定した動画レコードを DB から削除
    - Blob 上のファイルも削除
    """
    video = db.query(LectureVideosTable).filter(
        LectureVideosTable.lecture_video_id == lecture_video_id
    ).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    # DB 削除
    db.delete(video)
    db.commit()

    # Blob 削除
    if video.video_url:
        delete_file_from_blob(video.video_url)

    return {"message": f"Deleted lecture video id={lecture_video_id}"}
