from domain.interfaces import IOrderRepository
from infrastructure.logging_service import Logger

class OrderRepository(IOrderRepository):
    def __init__(self, logger: Logger):
        self.logger = logger

    def save_order(self, order):
        self.logger.log(f"Order saved: {order.order_id}")
        # In a real application, implement database save logic here.
