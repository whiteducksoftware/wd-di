# Component-Based Design with Interfaces and Lifetimes

Component-based design focuses on building systems from loosely coupled, replaceable parts (components). In the context of DI, this often involves defining clear interfaces (contracts) for your services and then providing concrete implementations for these interfaces. Managing the lifetime of these components is also a crucial aspect.

---

## Interface-Driven Development

**Principle:**
Define interfaces (typically Abstract Base Classes - ABCs in Python) for your services. Register your concrete service implementations against these interfaces. This allows you to easily swap out implementations (e.g., for different environments or for testing) without changing the code that uses the service.

**Example:**

```python
from abc import ABC, abstractmethod
from wd.di import create_service_collection

# Create a service collection instance
sc = create_service_collection()

# Define an interface for user repository
class IUserRepository(ABC):
    @abstractmethod
    def get_user(self, user_id: str) -> dict:
        pass

# Implementation of the repository interface
@sc.singleton(IUserRepository) # Register UserRepository as the singleton for IUserRepository
class UserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        # In a real app, this would fetch from a database
        print(f"UserRepository: Getting user {user_id}")
        return {"id": user_id, "name": "John Doe"}

# Another possible implementation (e.g., for testing or a different data source)
# Note: To use a named registration or switch implementations, you might need
# to manage multiple ServiceCollection instances or clear and re-register for tests.
# Standard resolution gets the last registered default for an interface.
@sc.singleton(IUserRepository) # This would overwrite the previous registration for IUserRepository
class MockUserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        print(f"MockUserRepository: Getting user {user_id}")
        return {"id": user_id, "name": "Mock User"}

# --- Usage ---
# If MockUserRepository was registered last, it will be the one resolved:
provider = sc.build_service_provider()
user_repo = provider.get_service(IUserRepository)
print(user_repo.get_user("123"))
# Expected output if MockUserRepository was last:
# MockUserRepository: Getting user 123
# {'id': '123', 'name': 'Mock User'}

# To truly switch, you'd typically manage registrations carefully:
sc_default = create_service_collection()
@sc_default.singleton(IUserRepository)
class RealUserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "Real User from DB"}

sc_test = create_service_collection()
@sc_test.singleton(IUserRepository)
class TestDoubleUserRepository(IUserRepository):
    def get_user(self, user_id: str) -> dict:
        return {"id": user_id, "name": "Test User via Double"}

# In app code:
# provider_real = sc_default.build_service_provider()
# repo_real = provider_real.get_service(IUserRepository)

# In test code:
# provider_test = sc_test.build_service_provider()
# repo_test = provider_test.get_service(IUserRepository)
```

**When to use Interface-Driven Development:**
Always prefer to code against interfaces rather than concrete implementations when a component is likely to have multiple implementations (e.g., for different data sources, different external services) or when you want to improve testability by easily mocking dependencies.

---

## Lifetimes Matter

**Principle:**
Select service lifetimes based on the nature of the dependency and how it should be shared:

*   **`@sc.transient()` (Transient):** A new instance of the service is created every time it is requested from the service provider or injected as a dependency.
    *   **Use for:** Lightweight, stateless services or services that should not share state between different consumers within the same scope or across scopes.
*   **`@sc.singleton()` (Singleton):** Only one instance of the service is created for the entire lifetime of the service provider (application). This single instance is shared across all requests and scopes.
    *   **Use for:** Services that are expensive to create, stateless utility services, or services that need to maintain a global application state (use with caution for shared mutable state).
*   **`@sc.scoped()` (Scoped):** A new instance of the service is created once per scope. Within the same scope (e.g., a web request, or a manually created scope via `provider.create_scope()`), the same instance is reused. Different scopes will get different instances.
    *   **Use for:** Services that need to maintain state for a specific unit of work (like a web request or a transaction) but should be isolated between different units of work. Examples include database session/connection objects, or services holding request-specific cache.

**Example (Conceptual Registration):**

```python
from wd.di import create_service_collection
# For demonstration, assume IService and various implementations are defined.
# class IService:
#     def do_work(self): raise NotImplementedError
# class MyTransientServiceImpl(IService): 
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")
# class MySingletonServiceImpl(IService):
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")
# class MyScopedServiceImpl(IService):
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")

sc = create_service_collection()

# Manual registration (less common now with decorators but still possible):
# sc.add_transient(IService, MyTransientServiceImpl)
# sc.add_singleton(IService, MySingletonServiceImpl)
# sc.add_scoped(IService, MyScopedServiceImpl)

# Using decorators (preferred):
# @sc.transient(IService)
# class DecoratedTransient(IService): ...

# @sc.singleton(IService)
# class DecoratedSingleton(IService): ...

# @sc.scoped(IService)
# class DecoratedScoped(IService): ...

# If decorating the class itself as the service type:
# @sc.transient()
# class MyPlainTransientService:
#     def __init__(self): print(f"{type(self).__name__} created")
#     def do_work(self): print(f"{type(self).__name__} working")
```

**When to Choose Lifetimes:**
Carefully consider the statefulness and resource implications of your services. 
- Use **transient** for stateless services or those needing unique instances.
- Use **singleton** for shared, stateless utilities or for managing global state carefully.
- Use **scoped** for services that need to maintain state within a specific unit of work (like a request) and be disposed of afterward. 