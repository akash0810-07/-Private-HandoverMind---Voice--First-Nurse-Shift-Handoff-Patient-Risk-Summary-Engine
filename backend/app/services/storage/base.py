from abc import ABC, abstractmethod


class StorageBackend(ABC):
    @abstractmethod
    def save(self, file_obj, filename: str) -> str:
        """Persist the file and return a storage location/key."""
        raise NotImplementedError

    @abstractmethod
    def get_path(self, location: str) -> str:
        """Resolve a storage location to a readable local path (for STT)."""
        raise NotImplementedError

    @abstractmethod
    def delete(self, location: str) -> None:
        raise NotImplementedError
