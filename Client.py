import grpc
import sys

from Server_pb2_grpc import ServerStub
from Server_pb2 import Request, Response

address = 'localhost:' + str(sys.argv[1])
print(address)


with grpc.insecure_channel(address) as channel:
    while True:
        print('O que você deseja fazer?')
        option = int(input('1 -> CREATE\n2 -> READ\n3 -> UPDATE\n4 -> DELETE\n5 -> ENCERRAR\n'))

        if option == 5:
            break

        key = input('Digite a chave: ')
        serverStub = ServerStub(channel)

        if option == 1:
            value = input('Digite o valor: ')
            response = serverStub.create(Request(key=key, value=value))
            print(str(response))

        if option == 2:
            response = serverStub.read(Request(key=key))
            print(str(response))

        if option == 3:
            value = input('Digite o valor: ')
            response = serverStub.update(Request(key=key, value=value))
            print(str(response))
                
        if option == 4:
            response = serverStub.delete(Request(key=key))
            print(str(response))
