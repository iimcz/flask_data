from time import time, sleep
from .HandlerBase import HandlerBase
from ..data_sources.TimeSourceBase import TimeSourceBase
from flask_sock import Server
from matplotlib.pyplot import imsave
from uuid import uuid1
from os.path import join
import numpy as np


class TimeSeriesBrowser(HandlerBase):
    def __init__(self, ws: Server, datasource: TimeSourceBase, poll_interval=0, cache_size=100) -> None:
        super().__init__(ws)

        if not isinstance(datasource, TimeSourceBase):
            raise TypeError("Datasource has to be TimeSourceBase!")

        self.datasource = datasource
        self.cache = []
        self.cache_size = cache_size
        if poll_interval:
            self.receive_loop_threaded()
            self._poll_loop(poll_interval)
        else:
            self.datasource.on_data = self._on_data
            self.receive_loop()

    def _on_data(self, datapoint):
        self._send_datapoint(datapoint)

    def _poll_loop(self, interval):
        next_poll = time()
        while self.ws.connected:
            datapoint = self.datasource.poll()
            self._send_datapoint(datapoint)

            next_poll = next_poll + interval
            sleep_for = next_poll - time()
            if sleep_for > 0:
                sleep(sleep_for)

    def _send_datapoint(self, datapoint):
        self.cache.append(datapoint)
        if len(self.cache) > self.cache_size:
            self.cache.pop(0)

        if not self.ws.connected:
            return
        if isinstance(datapoint, list):
            data = ','.join([str(x) for x in datapoint])
        else:
            data = str(datapoint)
        self.ws.send('data,time,' + data)

    def toimg(self):
        data = np.array(self.cache)

        if data.ndim == 1:
            data = np.array([[x] for x in data])
        filename = str(uuid1()) + '.png'
        imsave(join(self.static_folder, filename), data, cmap='gray')
        return f'link,{self.static_base_url + filename}'
