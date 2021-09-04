from flask_sock import Server
from threading import Thread


class HandlerBase:
    """
    This is a base class for implementing functionality accessible through flask_sock websockets.
    Incoming websocket text messages are converted to message calls. Messages are expected to be formatter like so:
      "fnname,arg0,arg1,..."
    HandlerBase then calls fnname on the derived class and then sends back the result via websocket. If successful,
    the result message starts with "data,fnname" and continues with comma-separated data points.
    On failure, a message starting with "err," is sent, containing an error massage afterwards.

    It is possible to disable the conversion from result to message (the derived class wants to send the message itself, or not at all)
    by passing result_to_response=False.
    """

    def __init__(self, ws: Server, result_to_response=True) -> None:
        self.ws = ws
        self.result_to_response = result_to_response

    def receive_loop(self):
        """
        Start listening to websocket messages and block until disconnected.
        """
        self._thread_fn()

    def receive_loop_threaded(self):
        """
        Same as receive_loop but spawns a separate thread, so it doesn't block.
        Useful when the derived class wants to send data itself periodically, not only as call results.
        """
        self.thread = Thread(target=self._thread_fn)
        self.thread.start()

    def _handle_command(self, cmd):
        fn, *args = cmd

        if fn in self.__class__.__dict__ and callable(self.__class__.__dict__[fn]):
            try:
                resp = self.__class__.__dict__[fn](self, *args)
                if not self.result_to_response:
                    return
                if isinstance(resp, list):
                    self.ws.send(
                        f'data,{fn},{",".join([str(x) for x in resp])}')
                else:
                    self.ws.send(f'data,{fn},{resp}')
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
