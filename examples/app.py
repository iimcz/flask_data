from flask import Flask, request
from flask_sock import Sock, Server
from random import random
from time import sleep
from os.path import join

import csv

from flask_data.socket_handlers import DataSeriesBrowser, TimeSeriesBrowser
from flask_data.data_sources import CadWebDataSource

STATIC_URL = '/static/'
STATIC_FOLDER = './static'
CSV_FOLDER = './csv'

app = Flask(__name__, static_url_path=STATIC_URL, static_folder=STATIC_FOLDER)
sock = Sock(app)


@sock.route('/random')
def ws_random(ws: Server):
    while ws.connected:
        ws.send(str(random()))
        sleep(1)


@sock.route('/csv/<filename>')
def ws_csv(ws: Server, filename):
    data = []
    with open(join(CSV_FOLDER, filename), 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for row in reader:
            data.append([float(x) for x in row])
    DataSeriesBrowser(ws, data, STATIC_FOLDER, request.host_url + STATIC_URL)


@sock.route('/cadweb')
def ws_cadweb(ws: Server):
    TimeSeriesBrowser(ws, CadWebDataSource(
        2, ['Yellow Intensity', 'Blue Intensity']))


if __name__ == '__main__':
    app.run(host='0.0.0.0')
