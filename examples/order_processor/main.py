from domain.interfaces import IOrderRepository, IOrderService
from wd.di import ServiceCollection
from wd.di.config import Configuration, IConfiguration
from infrastructure.config import AppConfig
from infrastructure.logging_service import Logger
from data.repository import OrderRepository
from services.order_service import OrderService
from presentation.controller import OrderController

services = ServiceCollection()

# Configure application settings
config = Configuration({
    "app": {
        "debug": True,
        "emailServer": "smtp.example.com"
    }
})
services.add_singleton_factory(IConfiguration, lambda _: config)
services.configure(AppConfig, section="app")

# Register infrastructure services
services.add_instance(Logger, Logger())

# Register data access layer (repository)
services.add_singleton(IOrderRepository, OrderRepository)

# Register business logic (order service)
services.add_singleton(IOrderService, OrderService)

# Register presentation layer (controller)
services.add_transient(OrderController)

# Build the service provider
provider = services.build_service_provider()

# Resolve the controller and simulate an order submission
controller = provider.get_service(OrderController)
controller.submit_order("order001", "Widget", 5, 19.99)
