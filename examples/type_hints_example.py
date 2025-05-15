from wd.di import ServiceCollection

services = ServiceCollection()

# Define interfaces and implementations
class IEmailService:
    def send_email(self, to: str, subject: str, body: str) -> None:
        pass

class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"\nSending email to {to}")
        print(f"Subject: {subject}")
        print(f"Body: {body}")
        print("Email sent successfully\n")

# UserService depends on IEmailService
class UserService:
    def __init__(self, email_service: IEmailService):
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str) -> None:
        self.email_service.send_email(f"user{user_id}@example.com", "Notification", message)

# Register services
services.add_singleton(IEmailService, EmailService)
services.add_singleton(UserService)

# Build provider
# Services will be resolved and injected into services 
# like EmailService into UserService
provider = services.build_service_provider()

# Get services with proper type hints
email_service = provider.get_service(IEmailService)
user_service = provider.get_service(UserService)

# IDE will provide code completion for these methods
# No need to cast or use Any
email_service.send_email("test@example.com", "Test", "Hello")
user_service.notify_user("123", "Welcome!")
