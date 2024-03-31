class OutOfStockError(Exception):
    def __init__(self, message="No hay suficiente stock disponible"):
        self.message = message
        super().__init__(self.message)