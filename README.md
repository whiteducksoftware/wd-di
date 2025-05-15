# WD-DI: .NET Style Dependency Injection for Python

WD-DI is a lightweight dependency injection library for Python inspired by .NET's DI system. It provides a robust and flexible way to manage dependencies and lifetimes in your applications. For the python purists: WD-DI needs no external libraries, just python std libraries.

Check this README.md for an overview of patterns supported by WD-DI.

[design_tutorial.md](./docs/design_tutorial.md) should provide some material for beginners on how to use DI to have a real positive impact on your software

[todo_until_feature_complete.md](./docs/todo_until_feature_complete.md) lists todos needed to be done to be feature congruent to .NET


---

## Features

WD-DI supports a variety of dependency injection patterns and configurations, including service lifetimes, constructor injection, configuration binding, middleware pipelines, and advanced lifetime management. Each feature comes with clear examples and guidance.

---

### 1. Service Lifetimes

**What is it?**  
Service lifetimes define how instances of services are created and shared. WD-DI supports three lifetimes:

- **Transient:** A new instance is created every time the service is requested.
- **Singleton:** A single instance is created and shared across the entire application.
- **Scoped:** A single instance is created for a specific scope (e.g., per web request).

**Example:**

```python
from wd.di import ServiceCollection

# Instantiate the collection
services = ServiceCollection()

# Register services with explicit implementation types:
services.add_transient(IService, ServiceImpl)   # Transient service
services.add_singleton(IService, ServiceImpl)   # Singleton service
services.add_scoped(IService, ServiceImpl)      # Scoped service

# Register service as self-implementing:
services.add_singleton(ServiceImpl)

# Using decorators for cleaner registration:
# Decorators are now methods on the ServiceCollection instance

@services.singleton()
class MyService:
    def do_something(self):
        pass

@services.transient()
class PerRequestService:
    def do_something(self):
        pass

@services.scoped()
class ScopedService:
    def do_something(self):
        pass
```

**When to use:**  
- Use **Transient** for lightweight, stateless services.
- Use **Singleton** for services that should be shared and reused.
- Use **Scoped** for services tied to a specific context, such as a web request.

---

### 2. Dependency Injection (Constructor Injection)

**What is it?**  
WD-DI uses constructor injection to automatically resolve and inject dependencies into your services. This promotes clear, testable, and maintainable code.

**Example:**

```python
from wd.di import ServiceCollection

services = ServiceCollection()

# Assume DatabaseService is defined and registered, e.g.:
# @services.singleton()
# class DatabaseService:
#     def query(self, sql: str): ...

@services.singleton()
class UserService:
    def __init__(self, db_service: DatabaseService):
        self.db = db_service

    def get_user(self, user_id: str):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# Build the service provider and resolve services:
provider = services.build_service_provider()
user_service = provider.get_service(UserService)

# with working code completion and resolved type for everything get_service returns!
# see examples/type_hints_example.py
```

**When to use:**  
Always prefer constructor injection—it makes dependencies explicit and simplifies unit testing.

---

### 3. Configuration and Options Pattern

**What is it?**  
WD-DI provides a configuration system that binds configuration data to strongly-typed options classes. This pattern helps centralize configuration logic and provides type safety.

**Example:**

```python
from dataclasses import dataclass
from wd.di import ServiceCollection
from wd.di.config import Configuration, Options, IConfiguration

services = ServiceCollection()

# Define an options class for your configuration
@dataclass
class DatabaseOptions:
    connection_string: str = ""
    max_connections: int = 10

# Create configuration from a dictionary (or JSON/environment variables)
config_data = {
    "database": {
        "connectionString": "mysql://localhost:3306/mydb",
        "maxConnections": 100
    }
}
app_config = Configuration(config_data)

# Register the configuration service
services.add_singleton_factory(IConfiguration, lambda _: app_config)

# Bind the configuration to strongly-typed options
services.configure(DatabaseOptions, section="database")

# Use the options in your service
@services.singleton()
class DatabaseService:
    def __init__(self, options: Options[DatabaseOptions]):
        self.connection_string = options.value.connection_string
        self.max_connections = options.value.max_connections
```

**When to use:**  
Use strongly-typed options to manage application settings and configurations in a clean, centralized way.

---

### 4. Middleware Pipeline

**What is it?**  
The middleware pipeline allows you to compose processing logic in a sequence. This is ideal for cross-cutting concerns such as logging, authentication, validation, caching, and error handling.

**Example:**

```python
from wd.di import ServiceCollection
from wd.di.middleware import IMiddleware, MiddlewarePipeline, LoggingMiddleware, ValidationMiddleware

services = ServiceCollection()

# Create custom middleware
class AuthMiddleware(IMiddleware):
    async def invoke(self, context, next):
        if not getattr(context, 'is_authenticated', False):
            raise ValueError("Not authenticated")
        return await next()

# Configure the middleware pipeline using a builder pattern:
app = services.create_application_builder()
app.configure_middleware(lambda builder: (
    builder
    .use_middleware(LoggingMiddleware)
    .use_middleware(AuthMiddleware)
    .use_middleware(ValidationMiddleware)
))

# Build the service provider and get the middleware pipeline:
provider = app.build()
pipeline = provider.get_service(MiddlewarePipeline)

# Execute the pipeline with a context object
# class MockContext: is_authenticated = True # Example context
# context = MockContext()
# result = await pipeline.execute(context)
```

**Built-in Middleware Components:**

- **LoggingMiddleware:** Logs pipeline execution.
- **ExceptionHandlerMiddleware:** Centralizes error handling.
- **ValidationMiddleware:** Validates the context.
- **CachingMiddleware:** Caches pipeline responses.

**When to use:**  
Use middleware pipelines to decouple and modularize cross-cutting concerns in your processing flows.

---

### 5. Scoped Services

**What is it?**  
Scoped services live only within a defined scope (e.g., a web request). WD-DI enforces explicit scope creation for such services and automatically disposes them when the scope ends.

**Example:**

```python
from wd.di import ServiceCollection

services = ServiceCollection()

# Assume MyService is defined and registered as scoped, e.g.:
# @services.scoped()
# class MyService: ...
# services.add_scoped(MyService) # Or using the decorator as shown above

provider = services.build_service_provider()

# Create a new scope
with provider.create_scope() as scope:
    # scoped_service = scope.get_service(MyService) # Assuming MyService is registered
    # Use the scoped service here
    pass # Placeholder
```

**When to use:**  
Use scoped services when you need to manage the lifetime of resources such as database connections or transaction contexts, ensuring proper cleanup at the end of the scope.

---

## Advanced Features

WD-DI also includes several advanced patterns that further extend its capabilities:

### Instance Registration

**What is it?**  
Register pre-created objects with the DI container. This is useful for sharing externally configured or created instances (like loggers or configuration objects).

**Example:**

```python
from wd.di import ServiceCollection

services = ServiceCollection()

class MyLogger:
    def log(self, msg):
        print(msg)

# Create and register an instance
logger_instance = MyLogger()
services.add_instance(MyLogger, logger_instance)

# Resolve and use the instance later:
provider = services.build_service_provider()
logger = provider.get_service(MyLogger)
assert logger is logger_instance  # True
logger.log("Instance registration works!")
```

**When to use:**  
Use instance registration when you need to inject a pre-configured or externally managed instance into your application.

---

### Circular Dependency Detection

**What is it?**  
Circular dependency detection safeguards your container against infinite recursion by detecting cycles in the dependency graph and raising a clear exception.

**Example:**

```python
from wd.di import ServiceCollection

services = ServiceCollection()

# Define services with a circular dependency
class ServiceA:
    def __init__(self, service_b: "ServiceB"):
        self.service_b = service_b

class ServiceB:
    def __init__(self, service_a: ServiceA):
        self.service_a = service_a

services.add_transient(ServiceA)
services.add_transient(ServiceB)

provider = services.build_service_provider()

try:
    provider.get_service(ServiceA)
except Exception as e:
    print(e)  # Output now includes: "Circular dependency detected for service: <class '__main__.ServiceA'>. Resolution stack: [...ServiceA..., ...ServiceB..., ...ServiceA...]
```

**When to use:**  
This feature works automatically. It's essential for catching configuration errors early during development when your dependency graph inadvertently contains cycles.

---

### Explicit Scoped Services Management

**What is it?**  
WD-DI enforces explicit scope creation and automatically disposes scoped services at the end of the scope. This ensures that resources are cleaned up properly.

**Example:**

```python
from wd.di import ServiceCollection

services = ServiceCollection()

# Define a disposable service
class DisposableResource:
    def __init__(self):
        self.disposed = False

    def dispose(self):
        self.disposed = True

@services.scoped()
class RegisteredDisposableResource(DisposableResource):
    pass

# services.add_scoped(DisposableResource) # Or like this, if not using decorator on distinct class
provider = services.build_service_provider()

# Create a new scope and resolve a scoped service:
with provider.create_scope() as scope:
    resource = scope.get_service(RegisteredDisposableResource)
    print(resource.disposed)  # False; resource is active

# After the scope, the resource is automatically disposed:
print(resource.disposed)  # True; dispose() was called
```

**When to use:**  
Scoped management is ideal when your services hold resources that need cleanup, such as file handles, database connections, or network sockets.

---

## Best Practices

1. **Constructor Injection:**  
   Always prefer constructor injection to clearly state dependencies and improve testability.

2. **Interface Segregation:**  
   Register services against interfaces to allow flexible swapping and better test isolation.

3. **Strongly-Typed Configuration:**  
   Use strongly-typed options for configuration to reduce runtime errors and centralize settings management.

4. **Middleware Separation:**  
   Keep middleware focused on a single responsibility to ensure composability and maintainability.

---

## Example Application

Below is a complete example that demonstrates how to set up and use WD-DI in a simple application:

```python
from dataclasses import dataclass
from wd.di import ServiceCollection
from wd.di.config import Configuration, Options, IConfiguration

services = ServiceCollection()

# Define interfaces
class IUserRepository:
    def get_user(self, user_id: str): pass

class IEmailService:
    def send_email(self, to: str, subject: str, body: str): pass

# Define configuration for email
@dataclass
class EmailOptions:
    smtp_server: str = ""
    port: int = 587
    username: str = ""
    password: str = ""

# Implement services
@services.singleton(IUserRepository)
class UserRepository(IUserRepository):
    def get_user(self, user_id: str):
        return {"id": user_id, "name": "John Doe", "email": "john@example.com"}

@services.singleton(IEmailService)
class EmailService(IEmailService):
    def __init__(self, options: Options[EmailOptions]):
        self.options = options.value

    def send_email(self, to: str, subject: str, body: str):
        print(f"Sending email via {self.options.smtp_server}")
        # Email sending logic here

@services.singleton()
class UserService:
    def __init__(self, repository: IUserRepository, email_service: IEmailService):
        self.repository = repository
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str):
        user = self.repository.get_user(user_id)
        self.email_service.send_email(
            to=user["email"],
            subject="Notification",
            body=message
        )

# Configure services and options
app_config = Configuration({
    "email": {
        "smtpServer": "smtp.gmail.com",
        "port": 587,
        "username": "myapp@gmail.com",
        "password": "secret"
    }
})

services.add_singleton_factory(IConfiguration, lambda _: app_config)
services.configure(EmailOptions, section="email")

# These are now redundant due to decorators specifying interfaces
# services.add_singleton(IUserRepository, UserRepository)
# services.add_singleton(IEmailService, EmailService)
# UserService is registered by its own decorator

# Build and use the service provider
provider = services.build_service_provider()
user_service = provider.get_service(UserService)
user_service.notify_user("123", "Hello, welcome to WD-DI!")
```


## License

This project is licensed under the terms of the LICENSE file included in the repository.