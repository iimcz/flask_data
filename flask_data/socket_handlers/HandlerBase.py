from flask_sock import Server
from threading import Thread


class HandlerBase:
    def __init__(self, ws: Server) -> None:
        self.ws = ws

    def receive_loop(self):
        self._thread_fn()

    def receive_loop_threaded(self):
        self.thread = Thread(target=self._thread_fn)
        self.thread.start()

    def _handle_command(self, cmd):
        fn, *args = cmd

        if fn in self.__class__.__dict__ and callable(self.__class__.__dict__[fn]):
            try:
                self.__class__.__dict__[fn](self, *args)
            except Exception as e:
                resp = f'err,Incorrect arguments for command {fn},{e}'
                self.ws.send(resp)
                print(resp)
        else:
            resp = f'err,Unknown command {fn}'
            self.ws.send(resp)
            print(resp)

    def _thread_fn(self):
        try:
            while self.ws.connected:
                data = self.ws.receive()
                if not data:
                    return
                if isinstance(data, bytes):
                    resp = 'err,Only accepts string messages!'
                    self.ws.send(resp)
                    print(resp)

                cmd = data.split(',')
                if len(cmd) == 0:
                    resp = 'err,Invalid command!'
                    self.ws.send(resp)
                    print(resp)

                self._handle_command(cmd)
        except:
            return
