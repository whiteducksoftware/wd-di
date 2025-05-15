# Advanced Example: Multi-Tenant Ingestion Service

This example demonstrates a more complex use case for `wd-di`, showcasing how to build a multi-tenant file ingestion service where each tenant uses a different cloud storage backend. It highlights features like scoped services, factory-based dependency resolution, `ContextVar` for managing tenant context, and configuration-driven behavior.

## 🌩️ The Scenario: Multi-Tenant Uploads

Imagine an ingestion service where *each* customer (tenant) insists on using their own cloud storage provider:

- **ACME Ltd.** → AWS S3
- **Contoso** → Azure Blob Storage
- **Globex** → Google Cloud Storage

At runtime, your application might receive an HTTP header like `X-Tenant-Id: ACME` and must dynamically choose and use the correct storage backend for that tenant.



## Why Use Dependency Injection for This?

Using `wd-di` for this scenario offers significant advantages over manual, conditional logic (e.g., large `if/elif` blocks):

-   **Pluggable Backends**: Adding a new tenant or storage provider (e.g., "DigitalOcean Spaces") becomes a matter of adding a new storage implementation class and updating a configuration mapping. No changes are needed in the core ingestion logic.
-   **Constructor Injection**: Storage backend implementations can themselves depend on other services (like a clock, logger, or authentication service). The DI container automatically resolves and injects these dependencies when creating a backend instance.
-   **Enhanced Testability**: During testing, you can easily swap out real cloud storage backends for a mock implementation (e.g., one that writes to the local file system or an in-memory store). This is done by simply registering the mock implementation in the `ServiceCollection` during test setup.

## Key DI Concepts Demonstrated

This example utilizes several important `wd-di` features:

1.  **`ServiceCollection`**: Used as the central registry for all service definitions (interfaces and their concrete implementations or factories).
2.  **`ContextVar` for Tenant ID**: A `contextvars.ContextVar` (`_current_tenant`) is used to implicitly carry the current tenant ID through asynchronous call chains without needing to pass it as an explicit parameter to every function.
3.  **Factory for Dynamic Resolution (`_storage_factory`)**: A factory function (`_storage_factory`) is registered for the `IBlobStorage` interface. This factory dynamically determines which concrete storage implementation to provide based on the current tenant's configuration (retrieved via `IConfiguration` and the `_current_tenant` context variable).
4.  **Service Lifetimes**: Careful selection of service lifetimes is crucial:
    *   `IClock`: Registered as a **singleton**. A single clock instance is shared across the entire application.
    *   `DataIngestionService`: Registered as **scoped**. A new instance is created for each logical request or operation scope (in this case, per tenant request).
        !!! info "Why is `DataIngestionService` Scoped and Not Singleton?"
            If `DataIngestionService` were a singleton, the DI container would create it once. When created, it would be injected with an `IBlobStorage` instance. Due to the factory logic, this would be the storage backend for the *very first tenant* whose request was processed. Subsequent requests for *other tenants* would erroneously reuse this same backend (e.g., all tenants' data might end up in ACME's S3 bucket). By making `DataIngestionService` scoped, a new instance is created within each tenant's request scope, ensuring it gets an `IBlobStorage` instance appropriate for *that specific tenant*.
    *   `IBlobStorage`: Registered with `add_transient_factory`. While the factory itself is called per resolution, the `DataIngestionService` being scoped means it gets its `IBlobStorage` once per scope. If `DataIngestionService` were transient, `IBlobStorage` (and its factory) would be resolved anew each time `DataIngestionService` was resolved.

## Application Workflow

1.  **Startup**: The main process initializes the `ServiceCollection` with all necessary service registrations and builds the root `ServiceProvider`.
2.  **Per Request (Simulated)**:
    1.  The `handle_request` function simulates an incoming request for a specific tenant.
    2.  The `_current_tenant` `ContextVar` is set to the ID of the tenant for the current request.
    3.  A new DI scope is created using `provider.create_scope()`. This ensures that any scoped services (like `DataIngestionService`) are fresh for this request.
    4.  `DataIngestionService` is resolved from the current scope. During its resolution:
        *   The DI container needs an `IBlobStorage`.
        *   It calls the registered factory for `IBlobStorage` (`_storage_factory`).
        *   The factory uses the `ServiceProvider` (`sp`) to get `IConfiguration` and the current tenant ID (from `_current_tenant.get()`) to determine the correct backend type (S3, Azure, GCS).
        *   It then instantiates and returns the appropriate concrete storage implementation (e.g., `S3Storage`), injecting its dependencies (like `IClock`).
    5.  The `ingest` method of the `DataIngestionService` is called to process the file, using the correctly injected tenant-specific storage backend.
    6.  Upon exiting the `with provider.create_scope() as scope:` block, the scope is disposed of. Any disposable scoped services would also be disposed.

This example is designed to be dependency-free for demonstration purposes; the "cloud" storage backends are simple in-memory classes. You can run `python examples/complex_ingest/app.py` (assuming the example structure) to see it in action.

## Implementation

```python
from contextvars import ContextVar
from typing import Dict, Callable, Type

from wd.di import ServiceCollection
from wd.di.config import Configuration, IConfiguration

# Placeholder interfaces/classes for self-contained documentation
class IClock:
    def now(self): ...

class IBlobStorage:
    def upload(self, blob_name: str, data: bytes): ...

class UtcClock(IClock):
    def now(self): return "current_time_utc" # Simplified

class S3Storage(IBlobStorage):
    def __init__(self, clock: IClock): self._clock = clock
    def upload(self, blob_name: str, data: bytes): print(f"S3: Uploading {blob_name} at {self._clock.now()} ({len(data)} bytes)")

class AzureBlobStorage(IBlobStorage):
    def __init__(self, clock: IClock): self._clock = clock
    def upload(self, blob_name: str, data: bytes): print(f"Azure: Uploading {blob_name} at {self._clock.now()} ({len(data)} bytes)")

class GcsStorage(IBlobStorage):
    def __init__(self, clock: IClock): self._clock = clock
    def upload(self, blob_name: str, data: bytes): print(f"GCS: Uploading {blob_name} at {self._clock.now()} ({len(data)} bytes)")

class DataIngestionService:
    def __init__(self, storage: IBlobStorage):
        self._storage = storage
    def ingest(self, filename: str, data: bytes):
        print(f"DataIngestionService: Ingesting {filename}")
        self._storage.upload(filename, data)


# 1. Set up the service collection
services = ServiceCollection()
services.add_singleton(IClock, UtcClock)
services.add_scoped(DataIngestionService)

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

_current_tenant: ContextVar[str] = ContextVar("tenant")

def _storage_factory(sp, tenant_id: str) -> IBlobStorage:
    backend = sp.get_service(IConfiguration).get(f"tenants:{tenant_id}:backend")
    mapping: Dict[str, Callable[[IClock], IBlobStorage]] = {
        "s3": lambda clock: S3Storage(clock),
        "azure": lambda clock: AzureBlobStorage(clock),
        "gcs": lambda clock: GcsStorage(clock),
    }
    if backend not in mapping:
        raise ValueError(f"Unknown backend \'{backend}\' for tenant {tenant_id}")
    return mapping[backend](sp.get_service(IClock))

services.add_transient_factory(
    IBlobStorage, lambda sp: _storage_factory(sp, _current_tenant.get())
)

provider = services.build_service_provider()

# 2. Request boundary helper
def handle_request(tenant_id: str, filename: str, data: bytes) -> None:
    token = _current_tenant.set(tenant_id)
    with provider.create_scope() as scope:
        scope.get_service(DataIngestionService).ingest(filename, data)
    _current_tenant.reset(token)

# 3. Demo run
if __name__ == "__main__":
    dummy_data = b"dummy file content"
    print("--- Simulating ACME request ---")
    handle_request("ACME", "acme/lucy.jpg", dummy_data)
    print("\n--- Simulating Contoso request ---")
    handle_request("Contoso", "contoso/luna.jpg", dummy_data)
    print("\n--- Simulating Globex request ---")
    handle_request("Globex", "globex/lucy.jpg", dummy_data)
```

This revised version should integrate much more smoothly into your MkDocs site. 