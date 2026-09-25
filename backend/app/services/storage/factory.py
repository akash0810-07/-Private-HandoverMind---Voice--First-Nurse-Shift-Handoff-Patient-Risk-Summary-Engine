from flask import current_app
from app.services.storage.local_backend import LocalStorageBackend
from app.services.storage.base import StorageBackend


def get_storage_backend() -> StorageBackend:
    backend = current_app.config.get("AUDIO_STORAGE_BACKEND", "local")
    if backend == "local":
        return LocalStorageBackend(current_app.config["AUDIO_STORAGE_PATH"])
    # Placeholder for a future S3StorageBackend implementing the same
    # StorageBackend interface — see docs/architecture.md.
    raise NotImplementedError(f"Storage backend '{backend}' is not implemented in v1.")
