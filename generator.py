

### 基本风格的10个get流程


import socket
import timeit
from concurrent import futures
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
selector = DefaultSelector()
stopped = False
urls_todo = {'/','/1','/2','/3','/4','/5','/6','/7','/8','/9'}




class Future(object):
    def __init__(self):
        self.result=None
        self._callbacks = []

    def add_done_callback(self,fn):
        self._callbacks.append(fn)

    def set_result(self,result):
        self.result=result
        for fn in self._callbacks:
            fn(self)



class Crawler(object):
    def __init__(self,url):
        self.url=url
        self.sock=None
        self.response = b''

    def fetch(self):
        self.sock=socket.socket()
        self.sock.setblocking(False)
        try:
            self.sock.connect(('cisco.com',80))
        except BlockingIOError:
            pass
        f = Future()
        def on_connected():
            f.set_result(None)

        selector.register(self.sock.fileno(), EVENT_WRITE, on_connected)
        yield f
        selector.unregister(self.sock.fileno())
        get = 'GET / HTTP/1.0\r\nHost: cisco.com\r\n\r\n'
        self.sock.send(get.encode('ascii'))
        # selector.register(self.sock.fileno(), EVENT_READ, self.read_response)
        global stopped
        while True:
            f = Future()
            def on_readdable():
                f.set_result(self.sock.recv(4096))
            selector.register(self.sock.fileno(), EVENT_READ, on_readdable)
            chunk = yield f
            selector.unregister(self.sock.fileno())
            if chunk:
                self.response +=chunk
            else:
                urls_todo.remove(self.url)
                if not urls_todo:
                  stopped = True
                break


class Task(object):
    def __init__(self, obj):
        self.obj=obj
        f =Future()
        # f.set_result(None)
        self.step(f)

    def step(self, future):
        try:
            next_future = next(self.obj)
            # next_future = self.obj.send(future.result)
        except StopIteration:
            return
        next_future.add_done_callback(self.step)

def loop():
    # Event Loop
    while not stopped:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback()



if __name__ == '__main__':
    start = timeit.default_timer()

    for url in urls_todo:
        crawler=Crawler(url)
        Task(crawler.fetch())
    loop()
    # print(sync_way())
    stop = timeit.default_timer()
    print(stop-start)