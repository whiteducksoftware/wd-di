from abc import ABC, abstractmethod

class IOrderRepository(ABC):
    @abstractmethod
    def save_order(self, order):
        pass

class IOrderService(ABC):
    @abstractmethod
    def process_order(self, order):
        pass