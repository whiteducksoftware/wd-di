"""
Composition root:
* Builds the DI container.
* Creates a per-request scope containing the chosen tenant ID.
* Demonstrates three different tenants using three different backends.
"""

from contextvars import ContextVar
from typing import Dict, Callable, Type

from wd.di import ServiceCollection
from wd.di.config import Configuration, IConfiguration

from storage.abstractions import IBlobStorage, IClock
from storage.impl import UtcClock, S3Storage, AzureBlobStorage, GcsStorage
from pipeline.ingestor import DataIngestionService

# ------------------------------------------------------------------
# 1. Set up the service collection
# ------------------------------------------------------------------
services = ServiceCollection()

# Shared dependencies
services.add_singleton(IClock, UtcClock)

# DataIngestionService is *tenant-specific*: if we made it a singleton
# it would capture the first tenant’s IBlobStorage instance and reuse it
# for every subsequent request. Try it out by changing it to a singleton.
services.add_scoped(DataIngestionService)

# Tenant configuration – could come from a file/env in real life
services.add_singleton_factory(
    IConfiguration,
    lambda _: Configuration(
        {
            "tenants": {
                "ACME": {"backend": "s3"},
                "Contoso": {"backend": "azure"},
                "Globex": {"backend": "gcs"},
            }
        }
    ),
)

# ContextVar that stores the tenant ID for the current scope
_current_tenant: ContextVar[str] = ContextVar("tenant")

# Runtime selector -------------------------------------------------
def _storage_factory(sp, tenant_id: str) -> IBlobStorage:
    """
    Map the tenant’s configured backend to the concrete implementation.
    """
    backend = sp.get_service(IConfiguration).get(f"tenants:{tenant_id}:backend")

    mapping: Dict[str, Callable[[IClock], IBlobStorage]] = {
        "s3": lambda clock: S3Storage(clock),
        "azure": lambda clock: AzureBlobStorage(clock),
        "gcs": lambda clock: GcsStorage(clock),
    }

    if backend not in mapping:
        raise ValueError(f"Unknown backend '{backend}' for tenant {tenant_id}")

    return mapping[backend](sp.get_service(IClock))


# Register abstract factory with DI
services.add_transient_factory(
    IBlobStorage, lambda sp: _storage_factory(sp, _current_tenant.get())
)

# Build provider
provider = services.build_service_provider()

# ------------------------------------------------------------------
# 2. Request boundary helper
# ------------------------------------------------------------------
def handle_request(tenant_id: str, filename: str, data: bytes) -> None:
    """
    Simulates an HTTP request boundary: sets the tenant context, creates a
    DI scope, and processes the ingestion.
    """
    token = _current_tenant.set(tenant_id)
    with provider.create_scope() as scope:
        scope.get_service(DataIngestionService).ingest(filename, data)
    _current_tenant.reset(token)


# ------------------------------------------------------------------
# 3. Demo run
# ------------------------------------------------------------------
if __name__ == "__main__":
    handle_request("ACME", "examples/complex_ingest/assets/lucy.png", b"abc")
    handle_request("Contoso", "examples/complex_ingest/assets/luna.png", b"def")
    handle_request("Globex", "examples/complex_ingest/assets/lucy.png", b"ghi")
