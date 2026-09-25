import os
import uuid
from app.services.storage.base import StorageBackend


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage for development and single-node deployments.
    An S3StorageBackend implementing the same interface can be swapped in
    via app/services/storage/factory.py without touching calling code.
    """

    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(self.base_path, exist_ok=True)

    def save(self, file_obj, filename: str) -> str:
        ext = os.path.splitext(filename)[1]
        safe_name = f"{uuid.uuid4()}{ext}"
        full_path = os.path.join(self.base_path, safe_name)
        file_obj.save(full_path)
        return safe_name  # storage "key"

    def get_path(self, location: str) -> str:
        return os.path.join(self.base_path, location)

    def delete(self, location: str) -> None:
        full_path = self.get_path(location)
        if os.path.exists(full_path):
            os.remove(full_path)
