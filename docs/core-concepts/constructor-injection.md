# Constructor Injection

Constructor injection is the primary mechanism by which WD-DI manages and provides dependencies to your services. When a service is resolved, WD-DI inspects its constructor (`__init__` method), identifies the required dependencies based on type hints, and automatically supplies instances of those dependencies.

This pattern promotes clear, testable, and maintainable code by making a class's dependencies explicit in its constructor signature.

---

## How It Works

1.  **Service Registration:** You register your services (e.g., `DatabaseService`, `UserService`) with the `ServiceCollection`, specifying their lifetimes.
2.  **Type Hinting:** Your service constructors must use type hints for their parameters (e.g., `db_service: DatabaseService`). WD-DI uses these hints to know which registered service to inject.
3.  **Resolution:** When you request a service (e.g., `provider.get_service(UserService)`), WD-DI:
    *   Finds the registered entry for `UserService`.
    *   Inspects its `__init__` method.
    *   Sees it needs a `DatabaseService`.
    *   Resolves an instance of `DatabaseService` (according to its registered lifetime).
    *   Instantiates `UserService`, passing the `DatabaseService` instance into its constructor.
    *   Returns the fully constructed `UserService` instance.

---

## Example

Let's consider a `UserService` that depends on a `DatabaseService`.

```python
from wd.di import ServiceCollection

services = ServiceCollection()

# Assume DatabaseService is defined and registered, for example:
# (This could be an interface IUserService or a concrete class)
class IDatabaseService: # Using an interface for demonstration
    def query(self, sql: str):
        raise NotImplementedError

@services.singleton(IDatabaseService) # Registering concrete type for the interface
class ConcreteDatabaseService(IDatabaseService):
    def __init__(self):
        print("ConcreteDatabaseService created (singleton)")

    def query(self, sql: str):
        print(f"Executing query: {sql}")
        return [{"id": 1, "name": "Test User"}] # Dummy data

# UserService depends on IDatabaseService
@services.singleton() # UserService itself can be a singleton or other lifetime
class UserService:
    def __init__(self, db_service: IDatabaseService): # Dependency is type-hinted
        print("UserService created, injecting IDatabaseService.")
        self.db = db_service

    def get_user_data(self, user_id: int):
        return self.db.query(f"SELECT * FROM users WHERE id = {user_id}")

# --- Usage ---
# Build the service provider
provider = services.build_service_provider()

# Resolve the UserService
# WD-DI will automatically create and inject ConcreteDatabaseService
user_service = provider.get_service(UserService)

# Use the service
user_data = user_service.get_user_data(user_id=1)
print(f"User data retrieved: {user_data}")

# If you resolve IDatabaseService directly, you get the same singleton instance
db_instance = provider.get_service(IDatabaseService)
print(f"Is user_service.db the same as db_instance? {user_service.db is db_instance}")

# Expected Output:
# ConcreteDatabaseService created (singleton)
# UserService created, injecting IDatabaseService.
# Executing query: SELECT * FROM users WHERE id = 1
# User data retrieved: [{'id': 1, 'name': 'Test User'}]
# Is user_service.db the same as db_instance? True
```

In this example:
*   `ConcreteDatabaseService` is registered as a singleton for the `IDatabaseService` interface.
*   `UserService` declares its dependency on `IDatabaseService` in its constructor.
*   When `UserService` is resolved, WD-DI provides the singleton instance of `ConcreteDatabaseService`.

---

## Benefits of Constructor Injection

*   **Explicit Dependencies:** A class's dependencies are clearly listed in its constructor signature, making the class's requirements easy to understand.
*   **Improved Testability:** When unit testing, you can easily pass mock or stub implementations of dependencies directly to the constructor, isolating the class under test. For example:
    ```python
    # --- Defining services (simplified for testability example) ---
    from abc import ABC, abstractmethod

    class IEmailService(ABC):
        @abstractmethod
        def send_email(self, recipient: str, subject: str, body: str):
            pass

    class UserService:
        def __init__(self, email_service: IEmailService):
            self.email_service = email_service

        def notify_user(self, user_id: str, message: str):
            # In a real app, fetch user's email, etc.
            email_address = f"{user_id}@example.com"
            self.email_service.send_email(email_address, "Notification", message)

    # --- Test with a mock --- 
    class MockEmailService(IEmailService):
        def __init__(self):
            self.sent_emails = []

        def send_email(self, recipient: str, subject: str, body: str):
            print(f"MOCK: Sending email to {recipient} - Subject: {subject}")
            self.sent_emails.append({"to": recipient, "subject": subject, "body": body})

    def test_user_service_notification():
        mock_mailer = MockEmailService()
        # Manually inject the mock when creating UserService for the test
        user_service_for_test = UserService(email_service=mock_mailer)
        
        user_service_for_test.notify_user("testuser", "Your item has shipped!")
        
        assert len(mock_mailer.sent_emails) == 1
        assert mock_mailer.sent_emails[0]["to"] == "testuser@example.com"
        assert mock_mailer.sent_emails[0]["body"] == "Your item has shipped!"
        print("Test passed: UserService correctly used the mock email service.")

    # To run the test (typically done by a test runner like pytest):
    # test_user_service_notification()
    ```
*   **Loose Coupling:** Classes don't create their dependencies; they receive them. This reduces coupling between components.
*   **Compile-Time Safety (with Type Hints):** While Python is dynamically typed, type hints used for DI allow static analysis tools (like MyPy) to catch potential type mismatches early.
*   **Readability and Maintainability:** Makes the flow of dependencies through your application easier to trace and manage.

---

**When to use:**

Always prefer constructor injection for mandatory dependencies. It's the cleanest and most straightforward way to implement Inversion of Control and Dependency Injection. WD-DI is designed primarily around this pattern. 