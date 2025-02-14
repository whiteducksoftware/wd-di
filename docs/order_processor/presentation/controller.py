from domain.models import Order
from domain.interfaces import IOrderService

class OrderController:
    def __init__(self, order_service: IOrderService):
        self.order_service = order_service

    def submit_order(self, order_id, item, quantity, price):
        order = Order(order_id=order_id, item=item, quantity=quantity, price=price)
        self.order_service.process_order(order)
