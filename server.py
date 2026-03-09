import socket
import threading
import time
import random
from datetime import datetime

#config do server
SERVER = 'localhost'
PORT = 5000
ADDR = (SERVER, PORT)

#variavel global pro estado do motorista
estado_motorista = {
    "status": "livre",
    "posicao_fila": 1
}
total_motoristas = 0 # NOVO: contador para atualizar a posição
lock = threading.Lock()

def thread_recebe_comandos(conn, addr, posicao_privada):
    #thread 1: recebe comandos
    while True:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if not msg:
                break
            
            comando = msg.strip()
            
            #IFs para os comandos:
            if comando == ":status":
                #usamos o 'lock' sempre que formos ler ou escrever na variável global
                with lock:
                    status_atual = estado_motorista["status"]
                    #agora usamos a posicao_privada recebida na conexão
                    posicao = posicao_privada
                resposta_comando = f"Seu status atual é: {status_atual.upper()}. Sua posição na fila é: {posicao}."

            elif comando == ":accept":
                with lock:
                    if estado_motorista["status"] == "livre":
                        estado_motorista["status"] = "em corrida" # Altera a memória compartilhada
                        resposta_comando = "Corrida aceita com sucesso! Dirija com segurança."
                    else:
                        resposta_comando = "Você já está em uma corrida e não pode aceitar outra."

            elif comando == ":cancel":
                with lock:
                    if estado_motorista["status"] == "em corrida":
                        estado_motorista["status"] = "livre"
                        resposta_comando = "Corrida cancelada com sucesso!"
                    else:
                        resposta_comando = "Você não esta em uma corrida para cancelar"

            elif comando == ":quit":
                #encerrando a conexão
                resposta_comando = "Deslogando do sistema... Tchau!!!"
                resposta_final = f"Voce executou: [{comando}]\n{resposta_comando}\n"
                conn.sendall(resposta_final.encode('utf-8'))
                break
            else:
                resposta_comando = "Comando não reconhecido."
            #eco de confirmação 
            resposta = f"Voce executou: [{comando}]\n"
            conn.sendall(resposta.encode('utf-8'))
            conn.sendall(resposta_comando.encode('utf-8'))
            
        except ConnectionResetError:
            break
            
    print(f"[DESCONECTADO] {addr}")
    conn.close()

def thread_gera_corridas(conn):
    #thread 2: gera eventos
    while True:
        time.sleep(15) #espera 15 segundos pra gerar uma corrida
        
        with lock:
            if estado_motorista["status"] == "livre":
                #gerando dados aleatórios da corrida
                distancia_inicio = random.randint(1, 10)
                distancia_corrida = random.randint(5, 30)
                valor = random.uniform(10.0, 50.0)
                
                #formatando o alerta assíncrono
                alerta = f"\n[ALERTA UBER] Nova corrida! Distância até o passageiro: {distancia_inicio}km. Distância da viagem: {distancia_corrida}km. Valor: R${valor:.2f}\n> "
                
                try:
                    conn.sendall(alerta.encode('utf-8'))
                except:
                    break #se der erro, o cliente desconectou

def main():
    global total_motoristas #referenciando o contador global
    #bind e o listen
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"[INICIANDO] Servidor de chamadas rodando em {SERVER}:{PORT}")

    while True:
        #fica esperando o motorista conectar
        conn, addr = server.accept()
        
        #incrementa a posição a cada nova conexão
        with lock:
            total_motoristas += 1
            posicao_atual = total_motoristas
            
        print(f"[NOVA CONEXÃO] Motorista {addr} conectado. Posição na fila: {posicao_atual}")
        
        #envia a mensagem inicial obrigatória 
        horario_atual = datetime.now().strftime("%H:%M")
        conn.sendall(f"<{horario_atual}>: CONECTADO!!\n".encode('utf-8'))

        #inicia as Threads para lidar com esse motorista
        #passamos a posicao_atual como argumento para a thread
        t1 = threading.Thread(target=thread_recebe_comandos, args=(conn, addr, posicao_atual))
        t2 = threading.Thread(target=thread_gera_corridas, args=(conn,))
        
        t1.start()
        t2.start()

if __name__ == "__main__":
    main()
