from abc import ABC, abstractmethod
from wd.di import services
from wd.di.decorators import singleton

# Define interfaces
class IEmailService(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> None:
        pass

class IUserService(ABC):
    @abstractmethod
    def notify_user(self, user_id: str, message: str) -> None:
        pass

# Implementations with decorators
@singleton(IEmailService)  # Type hint works with interface
class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"Sending email to {to}")

@singleton(IUserService)  # Type hint works with interface
class UserService(IUserService):
    def __init__(self, email_service: IEmailService):  # Constructor injection with proper type
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str) -> None:
        self.email_service.send_email(f"user{user_id}@example.com", "Notification", message)

# Define interface for config service for better type safety
class IConfigService(ABC):
    @abstractmethod
    def get_config(self, key: str) -> str:
        pass

@singleton(IConfigService)  # Register with interface
class ConfigService(IConfigService):
    def get_config(self, key: str) -> str:
        return f"Config value for {key}"

# Service without interface - register directly with the class
class LogService:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")

# Register the concrete class
services.add_singleton(LogService)

# Build provider
provider = services.build_service_provider()

# Get services with proper type hints
log_service = provider.get_service(LogService)  # Type hints work for concrete class
email_service = provider.get_service(IEmailService)  # Type hints work for interface
user_service = provider.get_service(IUserService)    # Type hints work for interface
config_service = provider.get_service(IConfigService)  # Type hints work for interface

# Use the services (IDE provides code completion for all methods)
log_service.log("Application started")
email_service.send_email("test@example.com", "Test", "Hello")
user_service.notify_user("123", "Welcome!")
config_value = config_service.get_config("api_key")
log_service.log(f"Got config: {config_value}")
