# Service Lifetimes

Service lifetimes define how instances of services are created, shared, and disposed of by the `ServiceProvider`. WD-DI supports three distinct lifetimes, allowing you to control the instantiation behavior of your registered services precisely.

Choosing the correct lifetime is crucial for managing resources efficiently and ensuring predictable behavior in your application.

---

## Transient

**What is it?**  
A new instance of a transient service is created every time it is requested from the service container. This is the default lifetime if none is specified (though explicit declaration is always clearer).

**Characteristics:**
*   Each call to `provider.get_service(MyTransientService)` or resolution of `MyTransientService` as a dependency will result in a brand-new object.
*   Suitable for lightweight, stateless services where each consumer needs a unique instance.

**Example:**

```python
from wd.di import ServiceCollection

# Assume IRequestProcessor and RequestProcessorImpl are defined
# interface IRequestProcessor: ...
# class RequestProcessorImpl(IRequestProcessor): ...

services = ServiceCollection()

# Registering with explicit implementation type:
services.add_transient(IRequestProcessor, RequestProcessorImpl)

# Or, using the decorator on the class itself (if it implements itself):
@services.transient()
class UniqueOperationLogger:
    def __init__(self):
        import uuid
        self.operation_id = uuid.uuid4()
        print(f"Logger {self.operation_id} created.")

    def log(self, message: str):
        print(f"[{self.operation_id}] {message}")

# --- Usage ---
provider = services.build_service_provider()

logger1 = provider.get_service(UniqueOperationLogger)
logger2 = provider.get_service(UniqueOperationLogger)

print(f"Are loggers the same instance? {logger1 is logger2}")
# Expected Output:
# Logger <uuid1> created.
# Logger <uuid2> created.
# Are loggers the same instance? False
```

**When to use:**
*   Lightweight, stateless services.
*   Services that need to be unique for each user or processing unit (e.g., a request-specific calculator).
*   When you want to avoid any risk of shared state between different parts of your application using the same service type.

---

## Singleton

**What is it?**  
A single instance of a singleton service is created the first time it is requested (or when `build_service_provider` is called if pre-instantiation is configured, though WD-DI resolves lazily by default). This same instance is then shared across the entire application for all subsequent requests within the same service provider.

**Characteristics:**
*   The first resolution creates the instance; all subsequent resolutions return that same instance.
*   Suitable for services that are expensive to create, maintain a shared state, or represent a global resource (e.g., application configuration, logging service, database connection pool manager).

**Example:**

```python
from wd.di import ServiceCollection

# Assume IApplicationSettings and ApplicationSettingsImpl are defined
# interface IApplicationSettings: ...
# class ApplicationSettingsImpl(IApplicationSettings): def load_settings(self): print("Settings loaded.")

services = ServiceCollection()

# Registering with explicit implementation type:
services.add_singleton(IApplicationSettings, ApplicationSettingsImpl)

# Or, using the decorator:
@services.singleton()
class AppConfig:
    def __init__(self):
        print("AppConfig initialized (once).")
        self.api_key = "my-secret-key"

# --- Usage ---
provider = services.build_service_provider()

config1 = provider.get_service(AppConfig)
config2 = provider.get_service(AppConfig)

print(f"Config1 API Key: {config1.api_key}")
print(f"Are configs the same instance? {config1 is config2}")
# Expected Output:
# AppConfig initialized (once).
# Config1 API Key: my-secret-key
# Are configs the same instance? True
```

**When to use:**
*   Services that manage shared state (e.g., caches, application-wide counters).
*   Services that are expensive to initialize and can be reused (e.g., HTTP clients with connection pooling, database access layers).
*   Configuration objects or logging services.
*   **Caution:** Be mindful of thread safety if the singleton service has mutable state that can be accessed concurrently.

---

## Scoped

**What is it?**  
A single instance of a scoped service is created for each defined "scope." Within a given scope, all requests for the service will return the same instance. Different scopes will each get their own unique instance.

**Characteristics:**
*   WD-DI requires explicit scope creation using `provider.create_scope()`.
*   Scoped services are typically created once per scope and disposed of when the scope ends (if they implement a `dispose()` or `close()` method).
*   This lifetime is ideal for services that should share state within a specific unit of work (e.g., a web request, a transaction) but should be isolated between different units of work.

**Example:**

```python
from wd.di import ServiceCollection

# Assume IUnitOfWork and UnitOfWorkImpl are defined
# interface IUnitOfWork: ...
# class UnitOfWorkImpl(IUnitOfWork): def __init__(self): print("UnitOfWork created for scope.")

services = ServiceCollection()

# Registering with explicit implementation type:
services.add_scoped(IUnitOfWork, UnitOfWorkImpl)

# Or, using the decorator:
@services.scoped()
class RequestContext:
    def __init__(self):
        import uuid
        self.request_id = uuid.uuid4()
        print(f"RequestContext {self.request_id} created for current scope.")

# --- Usage ---
provider = services.build_service_provider()

print("--- Scope 1 ---")
with provider.create_scope() as scope1:
    context1_a = scope1.get_service(RequestContext)
    context1_b = scope1.get_service(RequestContext)
    print(f"Are context1_a and context1_b the same? {context1_a is context1_b}")

print("\\n--- Scope 2 ---")
with provider.create_scope() as scope2:
    context2_a = scope2.get_service(RequestContext)
    context2_b = scope2.get_service(RequestContext)
    print(f"Are context2_a and context2_b the same? {context2_a is context2_b}")
    print(f"Is context1_a the same as context2_a? {context1_a is context2_a}")

# Expected Output:
# --- Scope 1 ---
# RequestContext <uuid1> created for current scope.
# Are context1_a and context1_b the same? True
#
# --- Scope 2 ---
# RequestContext <uuid2> created for current scope.
# Are context2_a and context2_b the same? True
# Is context1_a the same as context2_a? False
```

**When to use:**
*   Services that manage resources tied to a specific unit of work, like database connections or transaction contexts, ensuring proper setup and cleanup per scope.
*   Services that need to maintain state for a particular operation or request but should not be shared globally.
*   In web applications, often used for services per HTTP request.

---

Understanding and correctly applying these service lifetimes is fundamental to building robust and efficient applications with WD-DI. 