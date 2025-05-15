# Separation of Concerns

**Principle:**
Break your application into components with clear responsibilities. Use constructor injection to make dependencies explicit and decouple components.

**Example:**

```python
from wd.di import create_service_collection

# Create a service collection instance
sc = create_service_collection()

# EmailService: A service responsible for sending emails
@sc.singleton() # Registering EmailService as a singleton
class EmailService:
    def send_email(self, recipient: str, subject: str, body: str):
        print(f"Sending email to {recipient} with subject '{subject}' and body '{body}'")

# UserService: Depends on EmailService for notifications
@sc.singleton()
class UserService:
    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    def notify(self, user_id: str, message: str):
        # In a real app, fetch user's email from a repository, etc.
        email_address = f"{user_id}@example.com" # Example email
        self.email_service.send_email(email_address, "Notification", message)

# Register and use the services:
provider = sc.build_service_provider()
user_service = provider.get_service(UserService)
user_service.notify("user123", "Your order has shipped!")

# Expected Output:
# Sending email to user123@example.com with subject 'Notification' and body 'Your order has shipped!'
```

**When to use:**
Apply separation of concerns to keep business logic distinct from infrastructure (e.g., sending emails, logging), making your code easier to maintain and test. 