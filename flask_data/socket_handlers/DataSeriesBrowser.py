import uuid

from werkzeug import datastructures
from .HandlerBase import HandlerBase
from uuid import uuid1
from flask import Flask
from flask_sock import Server
from threading import Thread
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

    def get(self, start, count):
        a = int(start)
        b = a + int(count)
        data = [str(x) for x in self.datasource[a:b]]
        self.ws.send('data,' + ','.join(data))

    def getrange(self, xstart, xend):
        if not self.datasource.ndim >= 2:
            raise IndexError
        start = int(xstart)
        end = int(xend)
        data = np.array(
            [x for x in self.datasource if start <= x[0] <= end]).flatten()
        data = [str(x) for x in data]
        self.ws.send('data,' + ','.join(data))

    def getxy(self, x, y):
        if not self.datasource.ndim == 2:
            raise IndexError
        self.ws.send('data,' + str(self.datasource[int(x), int(y)]))

    def getxyz(self, x, y, z):
        if not self.datasource.ndim == 3:
            raise IndexError
        self.ws.send('data,' + str(self.datasource[int(x), int(y), int(z)]))

    def length(self):
        self.ws.send('data,' + str(len(self.datasource)))

    def dims(self):
        self.ws.send('data,' + str(self.datasource.ndim))

    def shape(self):
        shape = [str(x) for x in self.datasource.shape]
        self.ws.send('data,' + ','.join(shape))

    def toimg(self):
        if self.datasource.ndim == 1:
            data = np.array([[x] for x in self.datasource])
        else:
            data = self.datasource
        filename = str(uuid1()) + '.png'
        imsave(join(self.static_folder, filename), data, cmap='gray')
        self.ws.send('link,' + self.static_base_url + filename)

    def toimglimited(self, start, count):
        filename = str(uuid1()) + '.png'
        a = int(start)
        b = int(count)
        data = self.datasource[a:b]
        imsave(join(self.static_folder, filename), data, cmap='gray')
        self.ws.send('link,' + self.static_base_url + filename)
