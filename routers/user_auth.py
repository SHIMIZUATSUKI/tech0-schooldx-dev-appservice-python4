from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import AnswerDataTable
from schemas import AnswerDataRealtimeResponse


# デプロイテスト
# ユーザー認証用ルーター
router = APIRouter(
    prefix="/user_auth",
    tags=["user_auth"]
)