####### config.py

import os
from dotenv import load_dotenv
from urllib.parse import quote

load_dotenv()  # .env を読み込み

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
SSL_CERT_PATH = os.getenv("SSL_CERT_PATH")

# Azure Blob Storage
AZURE_ACCOUNT_NAME = os.getenv("AZURE_ACCOUNT_NAME")
AZURE_ACCOUNT_KEY = os.getenv("AZURE_ACCOUNT_KEY")
AZURE_BLOB_SERVICE_URL = os.getenv("AZURE_BLOB_SERVICE_URL")
AZURE_MOVIE_CONTAINER = os.getenv("AZURE_MOVIE_CONTAINER")

AZURE_ENVIRONMENT = os.getenv("AZURE_ENVIRONMENT")
NEXT_URL = os.getenv("NEXT_URL")

# CORS関連
raw_origins = os.getenv("ALLOWED_ORIGINS")  # 例: "http://xxx.azurewebsites.net,http://localhost:3000"

if raw_origins:
    ALLOWED_ORIGINS = [origin.strip() for origin in raw_origins.split(",")]
else:
    ALLOWED_ORIGINS = []

print("Allowed Origins:", ALLOWED_ORIGINS)

# Redis設定
def build_redis_url() -> str:
    """
    .env から Redis 接続情報を読み取り、python-socketio 用の REDIS_URL を組み立てる。
    Azure Managed Redis の場合:
      - TLS 必須 -> rediss://
      - ポート 10000
    """
    host = os.getenv("REDIS_HOST")
    password = os.getenv("REDIS_PASSWORD")

    if not host:
        raise RuntimeError("REDIS_HOST is not set in environment/.env")
    if not password:
        raise RuntimeError("REDIS_PASSWORD is not set in environment/.env")

    port = os.getenv("REDIS_PORT", "10000")
    db = os.getenv("REDIS_DB", "0")
    ssl = os.getenv("REDIS_SSL", "true").lower() == "true"

    scheme = "rediss" if ssl else "redis"

    # パスワードに記号が含まれても壊れないよう URL エンコード
    pw = quote(password, safe="")

    return f"{scheme}://:{pw}@{host}:{port}/{db}"


REDIS_URL = build_redis_url()
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "sio")