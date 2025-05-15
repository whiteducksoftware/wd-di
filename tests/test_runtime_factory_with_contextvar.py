"""
Full reproduction of the complex multi-tenant storage scenario, proving
that:

* each scope gets the right backend according to `tenant_id`
* IConfiguration (singleton) can be resolved inside the transient
  factory without circular-dependency issues
"""

from contextvars import ContextVar
from typing import Dict

from wd.di import ServiceCollection
from wd.di.config import IConfiguration, Configuration

# ── Abstractions & fake back-ends ----------------------------------

class IBlobStorage:
    def upload(self, path: str, data: bytes) -> str: ...

class InMemoryStore(IBlobStorage):
    def __init__(self, scheme: str):
        self.scheme = scheme
        self.objects: Dict[str, bytes] = {}

    def upload(self, path: str, data: bytes) -> str:
        self.objects[path] = data
        return f"{self.scheme}://bucket/{path}"

# ── Tenant-aware factory -------------------------------------------

_current_tenant: ContextVar[str] = ContextVar("tenant")

def storage_factory(sp, tenant_id: str) -> IBlobStorage:
    backend = sp.get_service(IConfiguration).get(
        f"tenants:{tenant_id}:backend"
    )
    mapping = {
        "s3":    lambda: InMemoryStore("s3"),
        "azure": lambda: InMemoryStore("azure"),
        "gcs":   lambda: InMemoryStore("gs"),
    }
    return mapping[backend]()

# ── Worker that depends on the storage -----------------------------

class DataIngestionService:
    def __init__(self, storage: IBlobStorage):
        self.storage = storage

    def ingest(self, file: str):
        return self.storage.upload(file, b"...")

# ── Test ------------------------------------------------------------

def test_tenant_specific_backend_via_contextvar_and_factory():
    services = ServiceCollection()

    services.add_singleton_factory(
        IConfiguration,
        lambda _:
            Configuration(
                {
                    "tenants": {
                        "ACME":    {"backend": "s3"},
                        "Contoso": {"backend": "azure"},
                        "Globex":  {"backend": "gcs"},
                    }
                }
            ),
    )

    services.add_scoped(DataIngestionService)  # per request
    services.add_transient_factory(
        IBlobStorage, lambda sp: storage_factory(sp, _current_tenant.get())
    )

    provider = services.build_service_provider()

    def run_for(tenant, file):
        token = _current_tenant.set(tenant)
        try:
            with provider.create_scope() as scope:
                return scope.get_service(DataIngestionService).ingest(file)
        finally:
            _current_tenant.reset(token)

    assert run_for("ACME",    "a.bin").startswith("s3://")
    assert run_for("Contoso", "b.jpg").startswith("azure://")
    assert run_for("Globex",  "c.pdf").startswith("gs://")
