from abc import ABC, abstractmethod
from dataclasses import dataclass
from wd.di import ServiceCollection
from wd.di.config import Configuration, IConfiguration

services = ServiceCollection()

# Define interfaces
class IEmailService(ABC):
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> None:
        pass

class IUserService(ABC):
    @abstractmethod
    def notify_user(self, user_id: str, message: str) -> None:
        pass



config = Configuration({
    "app": {
        "api_key": "real-secret-key"
    }
})

@dataclass
class AppConfig:
    api_key: str = "secret-key"

services.add_singleton_factory(IConfiguration, lambda _: config)
services.configure(AppConfig, section="app")

# Implementations with decorators
@services.singleton(IEmailService)
class EmailService(IEmailService):
    def send_email(self, to: str, subject: str, body: str) -> None:
        print(f"Sending email to {to}")

@services.singleton(IUserService)
class UserService(IUserService):
    def __init__(self, email_service: IEmailService):
        self.email_service = email_service

    def notify_user(self, user_id: str, message: str) -> None:
        self.email_service.send_email(f"user{user_id}@example.com", "Notification", message)



# Service without interface - register directly with the class
@services.singleton()
class LogService:
    def log(self, message: str) -> None:
        print(f"[LOG] {message}")

# Build provider
provider = services.build_service_provider()

# Get services with proper type hints
log_service = provider.get_service(LogService)
email_service = provider.get_service(IEmailService)
user_service = provider.get_service(IUserService)   
configuration = provider.get_service(IConfiguration) 


# Use the services (IDE provides code completion for all methods)
log_service.log("Application started")
email_service.send_email("test@example.com", "Test", "Hello")
user_service.notify_user("123", "Welcome!")
config_value = configuration.get("app:api_key")
log_service.log(f"Got config: {config_value}")
