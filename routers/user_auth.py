from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Dict, Optional

import pymysql
from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr

try:  # Only used when ID token verification is enabled
    from google.auth.transport import requests as google_requests
    from google.oauth2 import id_token as google_id_token
except ImportError:  # pragma: no cover - optional dependency
    google_requests = None
    google_id_token = None

logger = logging.getLogger("allowlist")
logging.basicConfig(level=logging.INFO)


class VerifyRequest(BaseModel):
    email: EmailStr


class VerifyResponse(BaseModel):
    allowed: bool


class Settings:
    """Simple settings loader backed by environment variables."""

    def __init__(self) -> None:
        self.mysql_host = os.getenv("AZURE_MYSQL_HOST", "")
        self.mysql_port = int(os.getenv("AZURE_MYSQL_PORT", "3306"))
        self.mysql_user = os.getenv("AZURE_MYSQL_USER", "")
        self.mysql_password = os.getenv("AZURE_MYSQL_PASSWORD", "")
        self.mysql_db = os.getenv("AZURE_MYSQL_DB", "")
        self.mysql_table = os.getenv("AZURE_MYSQL_TABLE", "allowed_users")
        self.require_id_token = os.getenv("REQUIRE_ID_TOKEN", "true").lower() not in {"false", "0", "no"}
        self.firebase_project_id = os.getenv("FIREBASE_PROJECT_ID")
        self.ssl_ca = os.getenv("AZURE_MYSQL_SSL_CA")

        for attr in ("mysql_host", "mysql_user", "mysql_password", "mysql_db"):
            if not getattr(self, attr):
                raise RuntimeError(f"Environment variable for {attr} is required")

    def connection_kwargs(self) -> Dict[str, object]:
        kwargs: Dict[str, object] = {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_db,
            "cursorclass": pymysql.cursors.DictCursor,
            "ssl": {"ca": self.ssl_ca} if self.ssl_ca else None,
            "charset": "utf8mb4",
            "use_unicode": True,
            "connect_timeout": 5,
            "read_timeout": 5,
            "write_timeout": 5,
        }
        if kwargs["ssl"] is None:
            kwargs.pop("ssl")
        return kwargs


def get_settings() -> Settings:
    return Settings()


@contextmanager
def mysql_connection(settings: Settings):
    conn = pymysql.connect(**settings.connection_kwargs())
    try:
        yield conn
    finally:
        conn.close()


def verify_id_token(token: str, settings: Settings) -> Optional[dict]:
    if not settings.require_id_token:
        return None
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    if google_requests is None or google_id_token is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="ID token verification dependencies are not installed")
    request = google_requests.Request()
    try:
        return google_id_token.verify_oauth2_token(token, request, audience=settings.firebase_project_id)
    except ValueError as exc:  # Raised when token is invalid/expired
        logger.warning("Invalid ID token: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID token") from exc


def email_allowed(email: str, settings: Settings) -> bool:
    query = f"SELECT 1 FROM `{settings.mysql_table}` WHERE email = %s LIMIT 1"
    with mysql_connection(settings) as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, (email,))
            return cursor.fetchone() is not None


def extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization header must be Bearer token")
    return authorization.split(" ", 1)[1].strip()


router = APIRouter()


@router.get("/healthz", tags=["meta"])
def health_check() -> dict:
    return {"status": "ok"}


@router.post("/verify", response_model=VerifyResponse)
def verify_user(
    payload: VerifyRequest,
    authorization: Optional[str] = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> VerifyResponse:
    token = extract_bearer_token(authorization)
    verify_id_token(token, settings)

    allowed = email_allowed(payload.email, settings)
    return VerifyResponse(allowed=allowed)

