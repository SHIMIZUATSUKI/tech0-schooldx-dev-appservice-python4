import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # CORS設定追加
from database import engine
from models import Base
from routers import lecture_videos, content, lesson_registration, lesson_attendance, answers_get_all, realtime_answers_put, answer_data_bulk, realtime_answers_get  # ★ 追加: answer_data_bulk
from config import ALLOWED_ORIGINS  # 環境変数として追加
from socket_server import sio_app  # ← 統合されたアプリをインポート
# 初回のみテーブルを自動作成（本番はAlembic等推奨）
# Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"],   # ここを変更
    allow_origins=ALLOWED_ORIGINS,   # config.pyのリスト
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
# ルータ登録
app.include_router(lecture_videos.router)
app.include_router(content.router)
app.include_router(lesson_registration.router)  # ✅ 統合されたルータを登録
app.include_router(lesson_attendance.router)  # ✅ 追加
app.include_router(answers_get_all.router)
app.include_router(realtime_answers_put.router)
app.include_router(answer_data_bulk.router)  # ★ 追加: 新機能ルーター
app.include_router(realtime_answers_get.router) # ✅ 追加
# Socket.IO を統合した ASGI アプリ
FastAPI_app = sio_app(app)
@app.get("/")
def root():
    return {"message": "Hello FastAPI + Socketio"}