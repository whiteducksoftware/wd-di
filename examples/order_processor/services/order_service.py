from domain.interfaces import IOrderService, IOrderRepository
from domain.models import Order
from infrastructure.logging_service import Logger

class OrderService(IOrderService):
    def __init__(self, repository: IOrderRepository, logger: Logger):
        self.repository = repository
        self.logger = logger

    def process_order(self, order: Order):
        self.logger.log(f"Processing order: {order.order_id}")
        # Business logic: validate order, process payment, etc.
        self.repository.save_order(order)
        self.logger.log(f"Order processed: {order.order_id}")
