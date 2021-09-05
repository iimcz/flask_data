from .HandlerBase import HandlerBase
from uuid import uuid1
from flask_sock import Server
from uuid import uuid1
from matplotlib.pyplot import imsave
from pathlib import Path
from os.path import join
import numpy as np


class DataSeriesBrowser(HandlerBase):
    def __init__(self, ws: Server, datasource, static_folder, static_base_url) -> None:
        super(DataSeriesBrowser, self).__init__(ws)

        if callable(datasource):
            datasource = datasource()
        if isinstance(datasource, list):
            datasource = np.array(datasource)
        self.datasource = datasource
        self.static_folder = static_folder
        self.static_base_url = static_base_url

        self.receive_loop()

    def getall(self):
        data = np.array(self.datasource).flatten()
        return data.tolist()

    def get(self, start, count):
        a = int(start)
        b = a + int(count)
        data = np.array(self.datasource[a:b]).flatten()
        return data.tolist()

    def getxrange(self, xstart, xend):
        if not self.datasource.ndim >= 2:
            raise IndexError
        start = int(xstart)
        end = int(xend)
        data = np.array(
            [x for x in self.datasource if start <= x[0] <= end]).flatten()
        return data.tolist()

    def getxy(self, x, y):
        if not self.datasource.ndim == 2:
            raise IndexError
        return self.datasource[int(x), int(y)]

    def getxyz(self, x, y, z):
        if not self.datasource.ndim == 3:
            raise IndexError
        return self.datasource[int(x), int(y), int(z)]

    def length(self):
        return len(self.datasource)

    def shape(self):
        return list(self.datasource.shape)

    def dims(self):
        return self.datasource.ndim

    def toimg(self, cmap):
        if self.datasource.ndim == 1:
            data = np.array([[x] for x in self.datasource])
        else:
            data = self.datasource
        filename = str(uuid1()) + '.png'
        imsave(join(self.static_folder, filename), data, cmap=cmap)
        return f'link,{self.static_base_url + filename}'

    def toimglimited(self, start, count, cmap):
        filename = str(uuid1()) + '.png'
        a = int(start)
        b = int(count)
        data = self.datasource[a:b]
        imsave(join(self.static_folder, filename), data, cmap=cmap)
        return f'link,{self.static_base_url + filename}'
