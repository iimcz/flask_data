class TimeSourceBase():
    def __init__(self) -> None:
        self.on_data = None

    def raise_on_data(self, datapoint):
        if self.on_data and callable(self.on_data):
            self.on_data(datapoint)

    def poll(self):
        pass
