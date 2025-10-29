import socketio
import asyncio

# ★ sio インスタンスをモジュールレベルで定義
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=["*"], # create_sio_app で上書きされます
    logger=True, 
    engineio_logger=True
)

# ★ sio_app もここで定義
sio_app = socketio.ASGIApp(sio)

# ★ 他のファイルから呼び出すための非同期ヘルパー関数
async def emit_to_web(event_name: str, data: any):
    """
    バックグラウンドタスクとしてSocket.IOイベントを発行する
    (PUT/POSTリクエストハンドラ内から呼び出す用)
    """
    try:
        # 'from_flutter' イベントとしてブロードキャスト
        print(f"Emitting event '{event_name}' with data: {data}")
        await sio.emit(event_name, data)
        print(f"Successfully emitted '{event_name}'")
    except Exception as e:
        print(f"Error emitting socket event: {e}")


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
        print("HTTP_ORIGIN  =", environ.get("HTTP_ORIGIN"))        

    @sio.event
    async def disconnect(sid):
        print(f"[disconnect] {sid}")

    # ★ sio_app インスタンスを返す
    return sio_app