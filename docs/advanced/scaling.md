# Scaling Your Application with WD-DI: Layered Architecture

Structuring your application into layers (e.g., Domain, Data Access, Application/Service, Presentation, Infrastructure) is a common and effective pattern for managing complexity and enhancing scalability and maintainability. WD-DI helps manage dependencies *between* these layers cleanly.

**Principle:**
Organize your code into distinct layers, each with a specific responsibility. Use Dependency Injection to provide dependencies to classes within a layer or from a lower layer to an upper layer. Avoid direct dependencies from lower layers to upper layers.

**Example: Layered Application**

Let's assume we have a `ServiceCollection` instance, `sc`, created via `sc = create_service_collection()`.

**Domain Layer:** Defines core business entities and interfaces.

```python
from abc import ABC, abstractmethod
# sc = create_service_collection() # Assume sc is available globally for these snippets for brevity

class IOrderService(ABC):
    @abstractmethod
    def process_order(self, order_id: str):
        pass

# OrderService would typically be in an Application/Service Layer
# For this example, let's imagine it's simple enough or defined elsewhere.
```

**Data Access Layer (Repository Pattern):** Handles data persistence.

```python
# from abc import ABC, abstractmethod # Already imported
# class IOrderService(ABC): ... # Defined above

class IOrderRepository(ABC):
    @abstractmethod
    def get_order(self, order_id: str) -> dict:
        pass
    @abstractmethod
    def save_order(self, order_data: dict):
        pass # Added save_order for completeness

# Example implementation for IOrderRepository
# @sc.singleton(IOrderRepository) # Decorator would be on the concrete class
# class OrderRepository(IOrderRepository):
#     def get_order(self, order_id: str) -> dict:
#         print(f"DAL: Getting order {order_id} from database.")
#         return {"id": order_id, "item": "Book from DB", "status": "Pending"}
#     def save_order(self, order_data: dict):
#         print(f"DAL: Saving order {order_data.get('id')} to database.")
```

**Application/Service Layer:** Contains business logic and orchestrates tasks, using services from the Domain and Data Access layers.

```python
# from abc import ABC, abstractmethod # Already imported
# class IOrderService(ABC): ... # Defined above
# class IOrderRepository(ABC): ... # Defined above

# @sc.singleton(IOrderService) # Decorator for OrderService implementation
# class OrderService(IOrderService):
#     def __init__(self, order_repo: IOrderRepository):
#         self.order_repo = order_repo
#
#     def process_order(self, order_id: str):
#         print(f"APP: Processing order {order_id}")
#         order = self.order_repo.get_order(order_id)
#         # ... some business logic ...
#         order["status"] = "Processed"
#         self.order_repo.save_order(order)
#         print(f"APP: Order {order_id} processed and saved.")
```

**Presentation Layer (e.g., Controller):** Handles user interaction or API requests and uses services from the Application Layer.

```python
# class IOrderService(ABC): ... # Defined above

# @sc.transient() # Controllers are often transient
# class OrderController:
#     def __init__(self, order_service: IOrderService):
#         self.order_service = order_service
#
#     def handle_web_request_for_order(self, order_id_from_request: str):
#         print(f"PRES: Received request for order {order_id_from_request}")
#         self.order_service.process_order(order_id_from_request)
#         print(f"PRES: Order {order_id_from_request} processing initiated.")
```

**Infrastructure Layer:** Contains cross-cutting concerns like logging, external service clients, etc. These can be injected into any layer where needed.

```python
# Example: A simple logger (could be more complex and registered via its own interface)
# @sc.singleton() # Registering a concrete logger as a singleton
# class ConsoleLogger:
#     def log(self, message: str):
#         print(f"[LOG] {message}")

# An OrderService might then take ILogger (if defined) or ConsoleLogger:
# class OrderService(IOrderService):
#     def __init__(self, order_repo: IOrderRepository, logger: ConsoleLogger):
#         self.order_repo = order_repo
#         self.logger = logger
#         # ... rest of the implementation ...
```

**Assembling and Running the Application (Illustrative)**

To make the above runnable, you'd need concrete classes and actual registration. Here's a more complete, self-contained example showing how these decorated classes would be registered and used:

```python
from abc import ABC, abstractmethod
from wd.di import create_service_collection

sc = create_service_collection()

# --- Interfaces (Domain Layer) ---
class IOrderRepository(ABC):
    @abstractmethod
    def get_order(self, order_id: str) -> dict:
        pass
    @abstractmethod
    def save_order(self, order_data: dict):
        pass

class IOrderService(ABC):
    @abstractmethod
    def process_order(self, order_id: str):
        pass

class ILogger(ABC):
    @abstractmethod
    def log(self, message: str):
        pass_a

# --- Implementations (Various Layers) ---
@sc.singleton(ILogger)
class ConsoleLogger(ILogger):
    def log(self, message: str):
        print(f"[LOG] {message}")

@sc.singleton(IOrderRepository)
class OrderRepository(IOrderRepository):
    def __init__(self, logger: ILogger):
        self.logger = logger

    def get_order(self, order_id: str) -> dict:
        self.logger.log(f"DAL: Getting order {order_id} from database.")
        return {"id": order_id, "item": "Book from DB", "status": "Pending"}
    
    def save_order(self, order_data: dict):
        self.logger.log(f"DAL: Saving order {order_data.get('id')} to database.")

@sc.singleton(IOrderService)
class OrderService(IOrderService):
    def __init__(self, order_repo: IOrderRepository, logger: ILogger):
        self.order_repo = order_repo
        self.logger = logger

    def process_order(self, order_id: str):
        self.logger.log(f"APP: Processing order {order_id}")
        order = self.order_repo.get_order(order_id)
        # ... some business logic ...
        order["status"] = "Processed"
        self.order_repo.save_order(order)
        self.logger.log(f"APP: Order {order_id} processed and saved.")

@sc.transient() # Controllers are often transient or scoped
class OrderController:
    def __init__(self, order_service: IOrderService, logger: ILogger):
        self.order_service = order_service
        self.logger = logger

    def handle_web_request_for_order(self, order_id_from_request: str):
        self.logger.log(f"PRES: Received request for order {order_id_from_request}")
        self.order_service.process_order(order_id_from_request)
        self.logger.log(f"PRES: Order {order_id_from_request} processing initiated.")

# --- Build and Run ---
provider = sc.build_service_provider()

controller = provider.get_service(OrderController)
controller.handle_web_request_for_order("order123")

# Expected Output:
# [LOG] PRES: Received request for order order123
# [LOG] APP: Processing order order123
# [LOG] DAL: Getting order order123 from database.
# [LOG] DAL: Saving order order123 to database.
# [LOG] APP: Order order123 processed and saved.
# [LOG] PRES: Order order123 processing initiated.
```

**When to use Layered Architecture:**
Build a layered architecture using WD-DI to cleanly separate business logic, data access, presentation, and infrastructure concerns. This enhances maintainability, testability (as layers can be tested in isolation by mocking adjacent layers), and scalability by allowing individual layers to be developed, deployed, and scaled independently (to some extent).

This approach helps in:
*   **Separation of Concerns:** Each layer has a well-defined responsibility.
*   **Maintainability:** Changes in one layer are less likely to impact other layers.
*   **Testability:** Layers can be tested independently by mocking dependencies from other layers.
*   **Scalability:** Different layers can potentially be scaled independently if the architecture allows (e.g., multiple instances of the presentation layer).

WD-DI facilitates this by making the dependencies between these layers explicit and manageable.

---

### Start Simple, Then Expand

**Principle:**
Begin with a minimal DI setup. As your project grows, you can introduce more sophisticated patterns like layered architectures, detailed interface-driven design, middleware pipelines, and dynamic configuration incrementally.

**Example:**

```python
from wd.di import create_service_collection
# Assume some services are defined, e.g.:
# class DatabaseService: ...
# class UserService: ...
# class LoggingMiddleware: # (from wd.di.middleware or custom)
#     async def invoke(self, context, next_call): ...

sc = create_service_collection()

# Initial phase: Register core services (decorators make this concise)
# @sc.singleton()
# class DatabaseService:
#     def connect(self):
#         print("DB Connected")
# @sc.singleton()
# class UserService:
#     def __init__(self, db: DatabaseService):
#         self.db = db
#     def get_user(self):
#         self.db.connect()
#         print("User fetched")

# provider = sc.build_service_provider()
# user_service = provider.get_service(UserService)
# user_service.get_user()

# Later, as the project evolves, integrate additional layers and middleware:
# (Assuming LoggingMiddleware is defined and UserService, DatabaseService are decorated)

# app_builder = sc.create_application_builder()
# app_builder.configure_middleware(lambda builder: (
#     builder.use_middleware(LoggingMiddleware) # Middleware needs to be DI-aware or resolvable
# ))
# # provider_with_middleware = app_builder.build()
# # Now, resolving services from provider_with_middleware will allow middleware pipeline execution (if pipeline is invoked)
```

**When to use:**
Adopt an incremental approach to DI. 
1. Start by registering your main services, perhaps using decorators for conciseness.
2. As complexity grows, introduce interfaces to decouple components further.
3. For cross-cutting concerns (logging, auth, error handling), implement a middleware pipeline.
4. Utilize the options pattern for robust configuration management as your application needs to support different environments or settings.

This evolutionary approach allows your architecture to adapt to the project's needs without over-engineering from the start. 