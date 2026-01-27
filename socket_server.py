import socketio
# import asyncio
import os
from datetime import datetime


from config import REDIS_URL, REDIS_CHANNEL


# Redis を Socket.IO の Client Manager として利用（Workers 複数での共有に必須）
mgr = socketio.AsyncRedisManager(
    REDIS_URL,
    write_only=False,
    channel=REDIS_CHANNEL,
)

# ★ sio インスタンスをモジュールレベルで定義
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["*"],  # create_sio_app で上書き
    logger=False,               # ログ出力の停止
    engineio_logger=False,     # ログ出力の停止
    client_manager=mgr,         # ★これが肝
    ping_interval=25,           # 任意：切断検知/維持を安定化
    ping_timeout=60,
)


# # ★ sio インスタンスをモジュールレベルで定義
# sio = socketio.AsyncServer(
#     async_mode="asgi",
#     cors_allowed_origins=["*"], # create_sio_app で上書きされます
#     logger=True, 
#     engineio_logger=True
# )

# ★ sio_app もここで定義
sio_app = socketio.ASGIApp(sio)

# ★ 他のファイルから呼び出すための非同期ヘルパー関数
async def emit_to_web(event_name: str, data: any):
    """
    バックグラウンドタスクとしてSocket.IOイベントを発行する
    (PUT/POSTリクエストハンドラ内から呼び出す用)
    """
    try:
        pid = os.getpid()
        print(f"[emit] pid={pid} event={event_name} data={data}")
        await sio.emit(event_name, data)
        print(f"[emit] pid={pid} OK")
    except Exception as e:
        print(f"[emit] pid={os.getpid()} ERROR: {e}")


def create_sio_app(cors_origins: list[str]):
    """
    CORS設定を適用し、イベントハンドラを登録する関数。
    """
    
    # ★ cors_allowed_origins を引数の値で上書き
    sio.cors_allowed_origins = cors_origins
    print(f"Socket.IO CORS Origins set to: {cors_origins}")

    # --- イベントハンドラ定義 ---
    @sio.event
    async def to_flutter(sid, data):
        print(f"[to_flutter] from {sid}: {data}")
        # 発信元（Web）を除いた全クライアントに送信
        await sio.emit('from_web', data, skip_sid=sid)

    @sio.event
    async def to_web(sid, data):
        print(f"[to_web] from {sid}: {data}")
        await sio.emit('from_flutter', data, skip_sid=sid)

    @sio.event
    async def connect(sid, environ):
        print(f"[connect] {sid}")
        # print("HTTP_ORIGIN  =", environ.get("HTTP_ORIGIN"))        

    @sio.event
    async def disconnect(sid):
        print(f"[disconnect] {sid}")

    # ★ sio_app インスタンスを返す
    return sio_app


# ログ出力用
@sio.event
async def connect(sid, environ, auth=None):
    pid = os.getpid()
    now = datetime.utcnow().isoformat()

    host = environ.get("HTTP_HOST")
    origin = environ.get("HTTP_ORIGIN")
    remote_addr = environ.get("REMOTE_ADDR")
    xff = environ.get("HTTP_X_FORWARDED_FOR")
    proto = environ.get("HTTP_X_FORWARDED_PROTO")

    # Engine.IO の query（transport など）
    query = environ.get("QUERY_STRING")

    print(
        f"[connect] utc={now} pid={pid} sid={sid} "
        f"host={host} origin={origin} remote={remote_addr} xff={xff} proto={proto} query={query}"
    )

@sio.event
async def disconnect(sid):
    print(f"[disconnect] pid={os.getpid()} sid={sid}")