####### config.py

import os
from dotenv import load_dotenv

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