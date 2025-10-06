import socketio

def create_sio_app(cors_origins: list[str]):
    """
    CORS設定を受け取り、設定済みのSocket.IO ASGIアプリケーションを生成する関数。
    """
    # Socket.IOサーバーのインスタンスを生成し、引数で受け取ったオリジンリストを設定
    sio = socketio.AsyncServer(
        async_mode="asgi",
        cors_allowed_origins=cors_origins
        # cors_allowed_origins="*"
    )

    # 既存のイベントハンドラを関数内に移動
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

    @sio.event
    async def disconnect(sid):
        print(f"[disconnect] {sid}")

    # FastAPIアプリとは独立したSocket.IOのASGIアプリを返す
    return socketio.ASGIApp(sio)