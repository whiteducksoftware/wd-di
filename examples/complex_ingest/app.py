"""
====================================================================
 🌩️  Multi-tenant “upload” demo — WHY dependency injection helps
====================================================================

Goal
----
Pretend you run an ingestion service where *each* customer (tenant)
insists on using their own cloud storage:

    ┌────────────┐          ┌─────────┐
    │  ACME Ltd. ├──►  AWS  │   S3    │
    ├────────────┤          └─────────┘
    │ Contoso    ├──► Azure Blob Storage
    ├────────────┤
    │  Globex    ├──► Google Cloud Storage
    └────────────┘

At runtime we receive an HTTP header like ``X-Tenant-Id: ACME`` and must
upload the file to *that* tenant's backend.

Why DI instead of if/elif spaghetti?
------------------------------------
* **Pluggable backends** - adding a new customer “DigitalOcean Spaces” is one mapping
  entry, no changes elsewhere.
* **Constructor injection** - a backend can depend on *other* services
  (clock, logger, auth) and the container wires everything up.
* **Easy testing** - swap real backends for an file system mock (like this demo)by
  registering a different implementation before
  ``build_service_provider()``.

Key moving parts in this file
-----------------------------
1. ``ServiceCollection`` - registers *what* can be built.
2. ``ContextVar`` *tenant* - carries the current tenant id through async
   calls without passing it as a parameter everywhere.
3. ``_storage_factory`` - looks up the tenant's backend in the
   configuration and returns the proper concrete class.
4. **Lifetimes**:
   * ``IClock``  → **singleton** (one for the whole app)
   * ``DataIngestionService`` → **scoped** (new per request / tenant)
     ◦ **Why not singleton?**  
       A singleton would hold on to whatever backend was injected for the
       *first* request and all tenants would end up in S3 (or whichever
       came first).

Workflow
--------
* Main process builds the root provider.
* Each request:
  1. sets ``_current_tenant``,
  2. opens a *scope* (so scoped services are fresh),
  3. resolves ``DataIngestionService`` which, via the factory, gets the
     right ``IBlobStorage`` for that tenant,
  4. uploads the file,
  5. disposes the scope.

Everything here is dependency-free: the “cloud” backends live in memory,
so you can `python app.py` and see it work instantly.

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
# it would capture the first tenant's IBlobStorage instance and reuse it
# for every subsequent request. Try it out by changing it to a singleton.
services.add_scoped(DataIngestionService)

# Tenant configuration - could come from a file/env in real life
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
    Map the tenant's configured backend to the concrete implementation.
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
    handle_request("ACME", "acme/lucy.jpg", open("examples/complex_ingest/assets/lucy.jpg", "rb").read())
    handle_request("Contoso", "contoso/luna.jpg", open("examples/complex_ingest/assets/luna.jpg", "rb").read())
    handle_request("Globex", "globex/lucy.jpg", open("examples/complex_ingest/assets/lucy.jpg", "rb").read())
