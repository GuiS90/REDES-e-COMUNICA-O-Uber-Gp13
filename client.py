import socket
import threading

PORT=5050
SERVER=socket.gethostbyname(socket.gethostname())
ADDR=(SERVER,PORT)

#aqui é o cliente iremos fazer um socket para ele tambem
CLIENT_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)

#aqui ele precisa se conectar ao nosso servidor
CLIENT_socket.connect(ADDR)