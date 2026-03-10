#VERSÃO FINAL ENTREGA 1
#importando o que precisamos
import socket
import threading
import sys

#configurações de rede (devem ser iguais às do servidor)
SERVER = 'localhost'
PORT = 5000
ADDR = (SERVER, PORT)

def thread_envia_comandos(client):
    #thread 1 do cliente: lê do teclado e envia
    while True:
        try:
            msg = input("> ")
            client.sendall(msg.encode('utf-8'))
            
            if msg.lower() == ':quit':
                client.close()
                sys.exit() #encerra o programa
        except:
            break

def thread_recebe_mensagens(client):
    #thread 2 do cliente: recebe notificações do servidor
    while True:
        try:
            msg = client.recv(1024).decode('utf-8')
            if not msg:
                break
            #imprime a mensagem recebida e recoloca o prompt "> " na tela
            print(f"\n{msg}", end="") 
        except:
            print("\n[ERRO] Conexão com o servidor foi perdida.")
            break

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        #conecta ao Servidor
        client.connect(ADDR)
        
        #recebe e imprime o horario e avisa que foi conectado 
        msg_inicial = client.recv(1024).decode('utf-8')
        print(msg_inicial)
        
        #inicia as threads do cliente
        t1 = threading.Thread(target=thread_envia_comandos, args=(client,))
        t2 = threading.Thread(target=thread_recebe_mensagens, args=(client,))
        
        #define como daemon (assim mesmo com loops ativos ele finaliza no quit) para que fechem se o programa principal fechar
        t1.daemon = True 
        t2.daemon = True
        
        t1.start()
        t2.start()
        
        #mantém a thread principal viva
        t1.join() 
        
    except ConnectionRefusedError:
        print("[ERRO] Não foi possível conectar. O servidor está rodando?")

if __name__ == "__main__":
    main()

