# Complex Ingestion Pipeline Example

This example demonstrates a multi-tenant data ingestion service that uses dependency injection to manage different storage backends for each tenant. It showcases how `wd-di` can be used to build flexible, pluggable, and testable systems.

## Scenario

Imagine an ingestion service where multiple customers (tenants) upload files. Each customer has their own preferred cloud storage provider:

*   **ACME Ltd.** uses AWS S3.
*   **Contoso** uses Azure Blob Storage.
*   **Globex Corp.** uses Google Cloud Storage.

When a file is uploaded, the system must determine the tenant (e.g., via an HTTP header like `X-Tenant-Id`) and route the file to the correct storage backend.

This example simulates this scenario, using in-memory mock implementations of the cloud storage services for simplicity and to allow the example to run without external dependencies.

## Key Concepts Demonstrated

*   **Dynamic Backend Selection**: Using a factory pattern (`_storage_factory` in `app.py`) in conjunction with DI to select the concrete `IBlobStorage` implementation at runtime based on the current tenant.
*   **Context-Aware Scoping**: Using `contextvars.ContextVar` to carry the current tenant ID through the call stack without explicit parameter passing, and leveraging DI scopes (`provider.create_scope()`) to ensure services like `DataIngestionService` are resolved with the correct tenant-specific dependencies.
*   **Service Lifetimes**: Demonstrates the use of different service lifetimes:
    *   `IClock` is registered as a **singleton** (one instance for the entire application).
    *   `DataIngestionService` is registered as **scoped** (a new instance per emulated request/tenant scope). This is crucial because if it were a singleton, it would capture the storage backend of the first tenant and incorrectly use it for all subsequent tenants.
    *   `IBlobStorage` is registered as **transient** (via `add_transient_factory`), meaning it's resolved (and the factory is called) each time it's requested within a scope.
*   **Configuration Management**: A simple `IConfiguration` service provides tenant-to-backend mappings, showcasing how DI can be used for managing application configuration.
*   **Pluggable Architecture**: The design makes it easy to add new tenants or storage backends by updating the configuration and the storage factory, with minimal changes to other parts of the system.
*   **Testability**: Although not explicitly shown with `pytest` tests in this example, the separation of concerns achieved through DI makes it straightforward to replace real storage backends with mocks for unit testing.

## Files and Structure

*   `app.py`: The main application script. It sets up the `ServiceCollection`, defines the tenant context, includes the storage factory logic, simulates request handling, and runs a demo.
*   `assets/`: Contains sample image files (`lucy.jpg`, `luna.jpg`) used for the simulated uploads.
*   `pipeline/`: Contains `ingestor.py` which likely defines `DataIngestionService` responsible for the ingestion logic.
*   `storage/`: 
    *   `abstractions.py`: Defines interfaces like `IBlobStorage` and `IClock`.
    *   `impl.py`: Provides concrete (mock) implementations for `S3Storage`, `AzureBlobStorage`, `GcsStorage`, and `UtcClock`.

## How it Works

1.  **Setup (`app.py`)**: 
    *   A `ServiceCollection` is initialized.
    *   Core services like `IClock` (singleton) and `DataIngestionService` (scoped) are registered.
    *   Tenant configuration (mapping tenant IDs to backend types like "s3", "azure", "gcs") is registered via `IConfiguration`.
    *   A `ContextVar` named `_current_tenant` is used to store the active tenant ID for each request.
    *   A factory function (`_storage_factory`) is defined. This factory consults `IConfiguration` and the `_current_tenant` to determine which concrete storage implementation (e.g., `S3Storage`) to instantiate. It then registers this factory for the `IBlobStorage` interface.
    *   The main `ServiceProvider` is built.

2.  **Request Handling (`handle_request` function in `app.py`)**:
    *   This function simulates an incoming request for a specific tenant.
    *   It sets the `_current_tenant` context variable.
    *   It creates a new DI scope from the root provider (`with provider.create_scope() as scope:`).
    *   Within this scope, it resolves `DataIngestionService`.
        *   When `DataIngestionService` is resolved, its dependencies are injected. If it depends on `IBlobStorage`, the DI container calls the registered factory for `IBlobStorage`.
        *   This factory (`_storage_factory`) reads `_current_tenant.get()` and creates the appropriate storage client (e.g., `S3Storage` for ACME).
    *   The `ingest` method of `DataIngestionService` is called to process the file.
    *   The scope is disposed upon exiting the `with` block.
    *   The tenant context is reset.

3.  **Demo Run (`if __name__ == "__main__":`)**:
    *   The `app.py` script, when run directly, calls `handle_request` for three different tenants (ACME, Contoso, Globex) with sample image data, demonstrating the dynamic selection of storage backends.

## Running the Example

Navigate to the `examples/complex_ingest` directory and run:

```bash
python app.py
```

You will see output indicating which tenant's data is being processed and which (mocked) storage backend is being used for each. For example:

```
[S3Storage] Storing lucy.jpg for tenant ACME...
[AzureBlobStorage] Storing luna.jpg for tenant Contoso...
[GcsStorage] Storing lucy.jpg for tenant Globex...
```

This example effectively illustrates the power of dependency injection in managing complex, context-dependent object graphs and promoting a modular, adaptable application architecture. 