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
    grade_summary
)
from socket_server import sio_app
from config import ALLOWED_ORIGINS

# FastAPIアプリケーション作成
app = FastAPI()

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Socket.IO統合
full_app = sio_app(app)

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

# ルートエンドポイント
@app.get("/")
def read_root():
    return {"message": "School DX API v3 Running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(full_app, host="0.0.0.0", port=port)