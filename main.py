import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine
from models import Base
# <<<<<<< HEAD
# from routers import lecture_videos, content, lesson_registration, lesson_attendance, answers_get_all, realtime_answers_put, answer_data_bulk, realtime_answers_get,user_auth  # ★ 追加: answer_data_bulk
# from config import ALLOWED_ORIGINS  # 環境変数として追加
# from socket_server import sio_app  # ← 統合されたアプリをインポート
# # 初回のみテーブルを自動作成（本番はAlembic等推奨）
# # Base.metadata.create_all(bind=engine)
# =======
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
# >>>>>>> 843fc589009a11daea744513a2f0eef21ffb30ae
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
# <<<<<<< HEAD
# app.include_router(answer_data_bulk.router)  # ★ 追加: 新機能ルーター
# app.include_router(realtime_answers_get.router) # ✅ 追加
# app.include_router(user_auth.router) # ✅ 追加
# # Socket.IO を統合した ASGI アプリ
FastAPI_app = sio_app(app)
# =======
app.include_router(answer_data_bulk.router)
app.include_router(realtime_answers_get.router)
app.include_router(classes.router)
app.include_router(grades.router)
app.include_router(grade_summary.router)

# ルートエンドポイント
# >>>>>>> 843fc589009a11daea744513a2f0eef21ffb30ae
@app.get("/")
def read_root():
    return {"message": "School DX API v3 Running"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(full_app, host="0.0.0.0", port=port)