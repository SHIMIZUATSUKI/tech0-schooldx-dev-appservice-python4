import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
from routers import (
    lecture_videos, content, lesson_registration, 
    lesson_attendance, answers_get_all, realtime_answers_put, 
    answer_data_bulk, realtime_answers_get,
    classes,
    grades,
    grade_summary,
    lessons,  # lessonsルーターをインポート
    lesson_themes # lesson_themesルーターをインポート
)
# 'sio_app' の代わりに新しいファクトリ関数 'create_sio_app' をインポート
from socket_server import create_sio_app
from config import ALLOWED_ORIGINS

# FastAPIアプリケーション作成
app = FastAPI()

# CORS設定 (これは主にHTTP APIリクエストに適用されます)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# --- Socket.IOの結合方法を修正 ---
# 1. ファクトリ関数を使って、設定ファイルから読み込んだオリジンを渡し、Socket.IOアプリを生成
sio_asgi_app = create_sio_app(cors_origins=ALLOWED_ORIGINS)

# 2. FastAPIアプリの '/socket.io' パスにSocket.IOアプリをマウント
# これにより、/socket.io/ へのリクエストは sio_asgi_app が処理する
app.mount('/socket.io', sio_asgi_app)
# --------------------------------

# ルーター登録
app.include_router(lecture_videos.router)
app.include_router(content.router)
app.include_router(lesson_registration.router)
app.include_router(lesson_attendance.router)
app.include_router(answers_get_all.router)
app.include_router(realtime_answers_put.router)
app.include_router(answer_data_bulk.router)
app.include_router(realtime_answers_get.router)
app.include_router(classes.router)
app.include_router(grades.router)
app.include_router(grade_summary.router)
app.include_router(lessons.router) # lessonsルーターを追加
app.include_router(lesson_themes.router) # lesson_themesルーターを追加

# ルートエンドポイント
@app.get("/")
def read_root():
    return {"message": "School DX API v3 Running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    # uvicornの実行対象を、マウント済みのFastAPIアプリ 'app' に変更
    uvicorn.run(app, host="0.0.0.0", port=port)