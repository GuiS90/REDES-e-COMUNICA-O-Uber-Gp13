#primeiro vamos fazer o nosso server.py
#vamos importar o que precisamos
import socket
import threading

#vamos fazer o socket do nosso server
PORT=5050
SERVER=socket.gethostbyname(socket.gethostname())
ADDR=(SERVER,PORT)
FORMAT='utf-8'
print("IP do servidor",SERVER,"\nPorta:",PORT)

#Agora iremos fazer o bind
SERVER_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
SERVER_socket.bind(ADDR)

#e o listen
SERVER_socket.listen()
print("o SERVER esta escutando")

#caso o cliente se conecte, mandar mensagem de confirmação e fechar o servidor
def handle_client(conn, addr):
    print(f"[NOVA CONEXAO] {addr} conectou.")
while True:
    conn, addr = SERVER_socket.accept()
    handle_client(conn, addr)