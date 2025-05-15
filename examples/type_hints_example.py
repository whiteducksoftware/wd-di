from abc import ABC, abstractmethod
from wd.di import ServiceCollection

services = ServiceCollection()

# Define interfaces and implementations
class IEmailService(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> None:
        pass

class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"Sending email to {to}")

class UserService:
    def __init__(self, email_service: IEmailService):
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str) -> None:
        self.email_service.send_email(f"user{user_id}@example.com", "Notification", message)

# Register services
services.add_singleton(IEmailService, EmailService)
services.add_singleton(UserService)

# Build provider
provider = services.build_service_provider()

# Get services with proper type hints
email_service = provider.get_service(IEmailService)  # Type hints work here
user_service = provider.get_service(UserService)      # And here

# IDE will provide code completion for these methods
email_service.send_email("test@example.com", "Test", "Hello")
user_service.notify_user("123", "Welcome!")
