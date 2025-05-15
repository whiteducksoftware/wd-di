# Getting Started with WD-DI 🚀

This guide will walk you through installing WD-DI and show you a quick example to get you up and running in minutes ⏱️.

## Installation 📦

WD-DI is available on PyPI. You can install it using pip:

```bash
pip install wd-di
```

That's it! 🎉 WD-DI has no external library dependencies, relying only on Python's standard library.

## 5-Minute Tutorial: Your First DI Application 🛠️

Let's build a very simple application to demonstrate the core concepts of WD-DI: registering services, injecting dependencies, and resolving them.

Imagine you have a `NotifierService` that needs an `IEmailService` to send notifications 📧.

```python
from wd.di import ServiceCollection

# 1. Create a service collection ⚙️
# This is the heart of your DI setup, managing all your service registrations.
services = ServiceCollection()

# 2. Define your services 📝
# It's good practice to define interfaces (Abstract Base Classes in Python)
# for your services to promote loose coupling.

class IEmailService:
    def send(self, message: str):
        """Interface for an email sending service."""
        raise NotImplementedError

# This is a concrete implementation of IEmailService.
# The @services.singleton(IEmailService) decorator registers this class
# as the singleton implementation for IEmailService. 🌍
@services.singleton(IEmailService)
class EmailService(IEmailService):
    def send(self, message: str):
        print(f"Sending email: {message}")

# NotifierService depends on IEmailService.
# The @services.transient() decorator means a new instance of NotifierService
# will be created each time it's requested. ⏳
@services.transient()
class NotifierService:
    # WD-DI will automatically inject an instance of IEmailService here. 💉
    def __init__(self, emailer: IEmailService):
        self._emailer = emailer

    def notify_admin(self, alert: str):
        self._emailer.send(f"Admin Alert: {alert}")

# 3. Build the service provider 🏭
# Once all services are registered, build the provider.
# The provider is responsible for resolving service instances.
provider = services.build_service_provider()

# 4. Resolve and use your services ✨
# Request an instance of NotifierService from the provider.
# WD-DI automatically infers the return type if using type hints.
notifier = provider.get_service(NotifierService)

# Now you can use your fully wired service.
notifier.notify_admin("System critical!")
# Expected Output:
# Sending email: Admin Alert: System critical!
```

**What happened here?** 🤔

1.  We created a `ServiceCollection` to hold our service registrations.
2.  We defined an interface `IEmailService` and its implementation `EmailService`. `EmailService` was registered as a singleton, meaning only one instance will be created and shared.
3.  We defined `NotifierService` which depends on `IEmailService`. It was registered as transient, meaning a new instance is created each time.
4.  When `NotifierService` was resolved, WD-DI saw its constructor required an `IEmailService`. It then looked up the registered implementation (`EmailService`), created/retrieved its instance, and passed it to the `NotifierService` constructor.
5.  The `notifier` instance we got back was fully formed with its `EmailService` dependency automatically handled. 👍

This simple example showcases the power of constructor injection and declarative service registration using decorators. Your components don't need to know how to create their dependencies; they just declare what they need, and WD-DI handles the rest.

## Next Steps 🗺️

You're now ready to explore more advanced features of WD-DI! 

*   Dive into **[Core Concepts](./core-concepts/lifetimes.md)** to understand service lifetimes, constructor injection in more detail, and configuration.
*   Learn about the **[Middleware Pipeline](./middleware/overview.md)** for handling cross-cutting concerns.
*   Explore the **[Tutorial](./tutorial/01-domain.md)** for a step-by-step guide to building a more complex application. 