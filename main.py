### 基本风格的10个get流程


import socket
import timeit
from concurrent import futures
from selectors import DefaultSelector, EVENT_READ, EVENT_WRITE
selector = DefaultSelector()
stopped = False
urls_todo = {'/','/1','/2','/3','/4','/5','/6','/7','/8','/9'}







class Crawler(object):
    def __init__(self,url):
        self.url=url
        self.sock=None
        self.response = b''

    def fetch(self):
        self.sock=socket.socket()
        self.sock.setblocking(False)
        try:
            self.sock.connect(('example.com',80))
        except BlockingIOError:
            pass
        selector.register(self.sock.fileno(), EVENT_WRITE, self.connected)

    def connected(self,key,mask):
        selector.unregister(key.fd)
        get = 'GET {0} HTTP/1.0\r\nHost: example.com\r\n\r\n'.format(self.url)
        self.sock.send(get.encode('ascii'))
        selector.register(key.fd, EVENT_READ, self.read_response)

    def read_response(self,key,mask):
        global stopped
        chunk = self.sock.recv(4096)
        if chunk:
            self.response+=chunk
        else:
            selector.unregister(key.fd)
            urls_todo.remove(self.url)
            if not urls_todo:
                stopped = True

def loop():
    # Event Loop
    while not stopped:
        events = selector.select()
        for event_key, event_mask in events:
            callback = event_key.data
            callback(event_key,event_mask)


# 多线程实现，受制于GIL，只适合IO敏感型应用
def multi_thread_way():
    workers = 10
    with futures.ThreadPoolExecutor(workers) as executor:
        futs = {executor.submit(block_way) for i in range(10)}
    return len([fut.result() for fut in futs])

# 多进程实现，受到切换时间的影响
def multi_process_way():
    workers = 10
    with futures.ProcessPoolExecutor(workers) as executor:
        futs={executor.submit(block_way) for i in range(10)}
    return len([fut.result() for fut in futs])


def nonblocking_way():
    sock = socket.socket()
    sock.setblocking(False)
    try:
        sock.connect(("127.0.0.1", 9010))
    except BlockingIOError:
        pass
    request = 'GET / HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n'
    data = request.encode('ascii')
    while True:
        try:
            sock.send(data)
            break
        except OSError:
            pass
    response = b''
    while True:
        try:
            chunk = sock.recv(4096)
            while chunk:
                response += chunk
                # Blocking
                chunk = sock.recv(4096)
            break
        except OSError:
            pass
    return response


def block_way():
    sock = socket.socket()

    sock.connect(("127.0.0.1", 9010))
    request = 'GET / HTTP/1.0\r\nHost: 127.0.0.1\r\n\r\n'
    sock.send(request.encode('ascii'))
    response = b''
    chunk = sock.recv(4096)
    while chunk:
        response += chunk
        # Blocking
        chunk = sock.recv(4096)
    return response

def sync_way():
    res = []
    for i in range(10):
        res.append(nonblocking_way())
    return len(res)


if __name__ == '__main__':
    start = timeit.default_timer()

    # for url in urls_todo:
    #     crawler=Crawler(url)
    #     crawler.fetch()
    # loop()
    print(multi_thread_way())
    stop = timeit.default_timer()
    print(stop-start)