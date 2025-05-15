# storage/impl.py
"""
Light-weight demo implementations for IBlobStorage.

* No external SDKs required.
* Files are persisted locally under ./uploads/<backend>/...
* Returned URI strings mimic the real cloud schemes (s3://, azure://, gs://).
"""

from __future__ import annotations

import datetime
import os
from pathlib import Path

from storage.abstractions import IBlobStorage, IClock


# ---------------------------------------------------------------------------
# Cross-cutting dependency
# ---------------------------------------------------------------------------

class UtcClock(IClock):
    def now(self) -> datetime.datetime:
        return datetime.datetime.utcnow()


# ---------------------------------------------------------------------------
# Helper: minimal local “object store”
# ---------------------------------------------------------------------------

def _write_file(root: str, path: str, data: bytes) -> Path:
    """
    Save *data* under ./uploads/<root>/<path> and return the Path object.
    """
    full_path = Path("examples/complex_ingest/uploads") / root / path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    full_path.write_bytes(data)
    return full_path


# ---------------------------------------------------------------------------
# Concrete storage back-ends (mocked)
# ---------------------------------------------------------------------------

class S3Storage(IBlobStorage):
    """
    Pretends to be AWS S3; bucket comes from $AWS_BUCKET or defaults to 'demo'.
    """

    def __init__(self, clock: IClock):
        self._clock = clock
        self._bucket = os.getenv("AWS_BUCKET", "demo")

    def upload(self, path: str, data: bytes) -> str:
        _write_file(f"s3/{self._bucket}", path, data)
        ts = self._clock.now().isoformat()
        return f"s3://{self._bucket}/{path}?ts={ts}"


class AzureBlobStorage(IBlobStorage):
    """
    Pretends to be Azure Blob Storage; container from $AZURE_CONTAINER or 'demo'.
    """

    def __init__(self, clock: IClock):
        self._clock = clock
        self._container = os.getenv("AZURE_CONTAINER", "demo")

    def upload(self, path: str, data: bytes) -> str:
        _write_file(f"azure/{self._container}", path, data)
        ts = self._clock.now().isoformat()
        return f"azure://{self._container}/{path}?ts={ts}"


class GcsStorage(IBlobStorage):
    """
    Pretends to be Google Cloud Storage; bucket from $GCP_BUCKET or 'demo'.
    """

    def __init__(self, clock: IClock):
        self._clock = clock
        self._bucket = os.getenv("GCP_BUCKET", "demo")

    def upload(self, path: str, data: bytes) -> str:
        _write_file(f"gcs/{self._bucket}", path, data)
        ts = self._clock.now().isoformat()
        return f"gs://{self._bucket}/{path}?ts={ts}"
