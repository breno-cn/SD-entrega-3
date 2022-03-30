import sys
import os
import signal
import grpc

from Server_pb2_grpc import ServerServicer, ServerStub, add_ServerServicer_to_server
from Server_pb2 import Request, Response
from Hashtable import Hashtable

from concurrent import futures

print(f'server pid: {os.getpid()}')

def calculateFingerTable(_signum, _frame):
    global serverServicer

    print(f'Calculating finger table of server {serverServicer.n}...')

    serverServicer.calculateFingerTable()

signal.signal(signal.SIGUSR1, calculateFingerTable)

def getHash(key: str):
    keyBytes = bytes(key, 'ascii')
    p = 31
    i = 0
    sum = 0

    for byte in keyBytes:
        sum += byte * (p ** i)
        i += 1

    return sum

def ping(address: str) -> bool:
    response = None
    try:
        channel = grpc.insecure_channel(address)
        stub = ServerStub(channel)
        stub.ping(Request())
        response = True
    except Exception as e:
        response = False
    finally:
        channel.close()
        return response

class Server(ServerServicer):
    
    def __init__(self, n: int, host: str, m: int) -> None:
        super().__init__()
        self.n = n
        self.host = host
        self.hashtable = Hashtable()
        self.m = m                      # ammount of bits used by the hash function, also determinate the max network size
        self.fingerTable = [0] * self.m
        self.maxNodes = (2 ** self.m) + 1

    def getResponsibleNode(self, key: str):
        result = getHash(key) % self.maxNodes
        print(result)

        for i in range(len(self.fingerTable)):
            if self.fingerTable[i] > result:
                possibleResponsible = self.fingerTable[0] if i == 0 else self.fingerTable[i - 1]
                return self.n if abs(self.n - result) < abs(possibleResponsible - result) else possibleResponsible

        return self.n

    def succ(self, addr: int):
        currentAddr = addr + 1
        while True:
            if ping(f'localhost:{currentAddr}'):
                return currentAddr
            currentAddr = (currentAddr + 1) % self.maxNodes

    def ping(self, request, context):
        return Response()

    def calculateFingerTable(self):
        for i in range(self.m):
            self.fingerTable[i] = self.succ((self.n + (2 ** (i))) % self.maxNodes)

        print(f'process {self.n} finger table: {self.fingerTable}')

    def create(self, request, context):
        key = request.key
        value = request.value

        node = self.getResponsibleNode(key)

        print(f'responsible node: {node}')

        if node == self.n:
            print(key, value, sep='\t')
            status = self.hashtable.create(key, value)
            return Response(status=status)

        with grpc.insecure_channel(f'localhost:{node}') as channel:
            stub = ServerStub(channel)
            return stub.create(Request(key=key, value=value))

    def read(self, request, context):
        key = request.key

        node = self.getResponsibleNode(key)

        print(f'responsible node: {node}')

        if node == self.n:
            response = self.hashtable.read(key)
            if type(response) == str:
                return Response(status=4, value=response)
            return Response(status=5)

        with grpc.insecure_channel(f'localhost:{node}') as channel:
            stub = ServerStub(channel)
            return stub.read(Request(key=key))

    def update(self, request, context):
        key = request.key
        value = request.value

        node = self.getResponsibleNode(key)

        print(f'responsible node: {node}')

        if node == self.n:
            print(key, value, sep='\t')
            status = self.hashtable.update(key, value)
            return Response(status=status, value=value)

        with grpc.insecure_channel(f'localhost:{node}') as channel:
            stub = ServerStub(channel)
            return stub.update(Request(key=key, value=value))

    def delete(self, request, context):
        key = request.key

        node = self.getResponsibleNode(key)

        print(f'responsible node: {node}')

        if node == self.n:
            status = self.hashtable.delete(key)
            return Response(status=status)

        with grpc.insecure_channel(f'localhost:{node}') as channel:
            stub = ServerStub(channel)
            return stub.delete(Request(key=key))


n = int(sys.argv[1])
m = int(sys.argv[2])
serverServicer = Server(n, 'localhost', m)
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

add_ServerServicer_to_server(serverServicer, server)

server.add_insecure_port(f'[::]:{n}')
server.start()

server.wait_for_termination()
