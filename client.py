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
                #encerra o socket e o programa
                client.close()
                sys.exit() 
        except:
            break

def thread_recebe_mensagens(client):
    #thread 2 do cliente: recebe notificações do servidor
    while True:
        try:
            msg = client.recv(1024).decode('utf-8')
            if not msg:
                break
            #imprime a mensagem recebida (pode ser alerta de corrida ou resposta de comando)
            print(f"\n{msg}", end="") 
        except:
            print("\n[ERRO] Conexão com o servidor foi perdida.")
            break

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    try:
        #conecta ao Servidor
        client.connect(ADDR)
        
        #recebe o pedido de identificação ou erro de lotação
        boas_vindas = client.recv(1024).decode('utf-8')
        
        #verifica se o servidor recusou por estar cheio
        if "ERRO" in boas_vindas:
            print(boas_vindas)
            client.close()
            return

        #lê o nome do motorista e envia para o servidor para persistência
        print(boas_vindas, end="")
        nome = input()
        client.sendall(nome.encode('utf-8'))

        #recebe e imprime a mensagem de confirmação final com horário
        msg_inicial = client.recv(1024).decode('utf-8')
        print(msg_inicial)
        
        #inicia as threads do cliente (cada cliente com 2 threads dedicadas)
        t1 = threading.Thread(target=thread_envia_comandos, args=(client,))
        t2 = threading.Thread(target=thread_recebe_mensagens, args=(client,))
        
        #define como daemon para que fechem se o programa principal fechar
        t1.daemon = True 
        t2.daemon = True
        
        t1.start()
        t2.start()
        
        #mantém a thread principal viva enquanto t1 rodar
        t1.join() 
        
    except ConnectionRefusedError:
        print("[ERRO] Não foi possível conectar. O servidor está rodando?")
    except KeyboardInterrupt:
        print("\n[SAINDO] Aplicação encerrada pelo usuário.")
        client.close()
        sys.exit()

if __name__ == "__main__":
    main()
