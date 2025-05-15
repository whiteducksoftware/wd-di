"""
Business layer that is agnostic of the concrete storage backend.
"""

from storage.abstractions import IBlobStorage


class DataIngestionService:
    def __init__(self, storage: IBlobStorage):
        self._storage = storage

    def ingest(self, filename: str, payload: bytes) -> None:
        uri = self._storage.upload(filename, payload)
        print(f"[INGEST] stored {filename} at {uri}")
