####### database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import urllib
import os

from config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, SSL_CERT_PATH

# SSL設定はconnect_argsだけで行う
ssl_args = {}
if SSL_CERT_PATH and os.path.exists(SSL_CERT_PATH):
    ssl_args = {"ssl_ca": SSL_CERT_PATH}

DB_URI = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"
    f"?charset=utf8mb4"
)

engine = create_engine(DB_URI, connect_args=ssl_args, echo=False)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()