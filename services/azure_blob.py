######## azure_blob.py
import uuid
import re
from azure.storage.blob import BlobServiceClient, ContentSettings
from config import (
    AZURE_ACCOUNT_NAME,
    AZURE_ACCOUNT_KEY,
    AZURE_BLOB_SERVICE_URL,
    AZURE_MOVIE_CONTAINER
)

def get_blob_service_client():
    """
    アカウント名・キー・エンドポイントURLから BlobServiceClient を生成
    """
    blob_service_client = BlobServiceClient(
        account_url=AZURE_BLOB_SERVICE_URL,
        credential=AZURE_ACCOUNT_KEY
    )
    return blob_service_client

def upload_file_to_blob(file_data: bytes, original_filename: str) -> str:
    """
    `movie-mvp` コンテナにファイルをアップロードし、Blob の公開 URL を返す。
    Content-Type を "video/mp4" に固定するサンプル実装。
    """
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(AZURE_MOVIE_CONTAINER)

    # 拡張子などを考慮したユニークファイル名
    ext = ""
    if "." in original_filename:
        ext = "." + original_filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}{ext}"

    blob_client = container_client.get_blob_client(unique_filename)

    # ContentSettings でContent-Typeを指定
    blob_client.upload_blob(
        file_data,
        overwrite=True,
        content_settings=ContentSettings(content_type="video/mp4"),
    )

    # アップロードした Blob の URL を返す
    return f"{AZURE_BLOB_SERVICE_URL}/{AZURE_MOVIE_CONTAINER}/{unique_filename}"

def delete_file_from_blob(blob_url: str):
    """
    Blob URL からファイル名を抜き出し、対応するファイルを削除する。
    例: https://xxx.blob.core.windows.net/movie-mvp/xxxx-uuid.mp4
    """
    pattern = rf"{AZURE_BLOB_SERVICE_URL}/{AZURE_MOVIE_CONTAINER}/(.+)"
    match = re.match(pattern, blob_url)
    if not match:
        # URL形式が想定外なら削除せず処理終了
        return

    filename = match.group(1)  # blob上のファイル名部分
    blob_service_client = get_blob_service_client()
    container_client = blob_service_client.get_container_client(AZURE_MOVIE_CONTAINER)

    container_client.delete_blob(filename)