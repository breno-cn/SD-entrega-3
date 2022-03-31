from fcntl import F_SEAL_SEAL
import sys
import os
import signal
import grpc

from Server_pb2_grpc import ServerServicer, ServerStub, add_ServerServicer_to_server
from Server_pb2 import Request, Response, Void, PingResponse
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
        pingResponse = stub.ping(Request())
        response = pingResponse.n
    except Exception as e:
        response = F_SEAL_SEAL
    finally:
        channel.close()
        return response

class Server(ServerServicer):
    
    def __init__(self, n: int, host: str, m: int, port: int) -> None:
        super().__init__()
        self.n = n
        self.host = host
        self.hashtable = Hashtable()
        self.m = m                      # ammount of bits used by the hash function, also determinate the max network size
        self.fingerTable = [0] * self.m
        self.maxNodes = (2 ** self.m) + 1
        self.port = port
        self.replicas = sys.argv[4:]              # TODO: receber o port dos outros servers do nó

        print(f'replicas of {self.port}: {self.replicas}')
        print(f'M: {self.m}')
        print(f'maxNodes: {self.maxNodes}')

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
            response = ping(f'localhost:{currentAddr}')
            if response != False and response != self.n:
                return currentAddr
            currentAddr = (currentAddr + 1) % self.maxNodes

    def ping(self, request, context):
        return PingResponse(self.n)

    # TODO: no ping, retornar o N, a posicao do server no anel lógico
    def calculateFingerTable(self):
        for i in range(self.m):
            self.fingerTable[i] = self.succ((self.n + (2 ** (i))) % self.maxNodes)

        print(f'process {self.port} finger table: {self.fingerTable}')

    def create(self, request, context):
        key = request.key
        value = request.value

        node = self.getResponsibleNode(key)

        print(f'responsible node: {node}')

        if node == self.n:
            print(key, value, sep='\t')

            # Replica a operação nos outros servidores do nó
            for replica in self.replicas:
                with grpc.insecure_channel(f'localhost:{replica}') as channel:
                    stub = ServerStub(channel)
                    stub.replicateCreate(request)

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

    def replicateCreate(self, request, context):
        key = request.key
        value = request.value

        self.hashtable.create(key, value)

        return Void()

    def replicateRead(self, request, context):
        return Void()

    def replicateUpdate(self, request, context):
        key = request.key
        value = request.value

        self.hashtable.update(key, value)

        return Void()

    def replicateDelete(self, request, context):
        key = request.key

        self.hashtable.delete(key)

        return Void()


n = int(sys.argv[1])
m = int(sys.argv[2])
port = int(sys.argv[3])
serverServicer = Server(n, 'localhost', m, port)
server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

add_ServerServicer_to_server(serverServicer, server)

server.add_insecure_port(f'[::]:{port}')
server.start()

server.wait_for_termination()
