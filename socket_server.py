import socketio
from config import ALLOWED_ORIGINS

sio = socketio.AsyncServer(
    async_mode="asgi",
    # 「*」（誰でもOK）から、設定ファイルで許可されたオリジンリストに変更します
    cors_allowed_origins=ALLOWED_ORIGINS
)


@sio.event
async def to_flutter(sid, data):
    print(f"[to_flutter] from {sid}: {data}")
    # 発信元（Web）を除いた全クライアントに送信
    await sio.emit('from_web', data, skip_sid=sid)

# Flutter → Web 用イベント
@sio.event
async def to_web(sid, data):
    print(f"[to_web] from {sid}: {data}")
    await sio.emit('from_flutter', data, skip_sid=sid)

@sio.event
async def connect(sid, environ):
    print(f"[connect] {sid}")

@sio.event
async def disconnect(sid):
    print(f"[disconnect] {sid}")

# ASGI 統合用の関数を提供
def sio_app(fastapi_app):
    return socketio.ASGIApp(sio, fastapi_app)
