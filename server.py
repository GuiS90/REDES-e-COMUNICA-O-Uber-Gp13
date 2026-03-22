import socket
import threading
import time
import random
import sys
import json
import os
from datetime import datetime

#configurações do server
SERVER = 'localhost'
PORT = 5000
ADDR = (SERVER, PORT)

#dicionário global para persistência em memória: {nome: {"saldo": 0.0}}
banco_motoristas = {}
ARQUIVO_DADOS = "motoristas.json"

#variáveis globais de controle
total_motoristas_online = 0
lock = threading.Lock()

def carregar_dados():
    """Carrega os dados do disco para a memória """
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, 'r') as f:
            return json.load(f)
    return {}

def salvar_dados():
    """Salva os dados da memória para o disco """
    with lock:
        with open(ARQUIVO_DADOS, 'w') as f:
            json.dump(banco_motoristas, f)

def thread_recebe_comandos(conn, addr, nome_motorista, posicao_privada):
    global total_motoristas_online
    #estado local da sessão deste motorista
    sessao = {"status": "livre", "ultima_corrida_valor": 0.0}
    
    while True:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if not msg: break
            
            comando = msg.strip()
            resposta_comando = ""

            if comando == ":status":
                with lock:
                    saldo = banco_motoristas[nome_motorista]["saldo"]
                resposta_comando = f"Status: {sessao['status'].upper()} | Faturamento Total: R${saldo:.2f} | Posição: {posicao_privada}" [cite: 106, 272]

            elif comando == ":accept":
                with lock:
                    if sessao["status"] == "livre":
                        sessao["status"] = "em corrida"
                        #simula o ganho sendo creditado 
                        valor = random.uniform(15.0, 45.0)
                        sessao["ultima_corrida_valor"] = valor
                        banco_motoristas[nome_motorista]["saldo"] += valor
                        salvar_dados()
                        resposta_comando = f"Corrida aceita! Valor de R${valor:.2f} será creditado ao finalizar." [cite: 111]
                    else:
                        resposta_comando = "Você já está em uma corrida."

            elif comando == ":cancel":
                with lock:
                    if sessao["status"] == "em corrida":
                        #estorna o valor se cancelado (lógica de exemplo)
                        banco_motoristas[nome_motorista]["saldo"] -= sessao["ultima_corrida_valor"]
                        sessao["status"] = "livre"
                        salvar_dados()
                        resposta_comando = "Corrida cancelada e valor estornado."
                    else:
                        resposta_comando = "Não há corrida para cancelar."

            elif comando == ":quit":
                resposta_comando = "Deslogando... Dados salvos."
                conn.sendall(f"Voce executou: [{comando}]\n{resposta_comando}\n".encode('utf-8'))
                break
            
            else:
                resposta_comando = "Comando não reconhecido."

            #eco de confirmação [cite: 111, 222]
            conn.sendall(f"Voce executou: [{comando}]\n{resposta_comando}\n> ".encode('utf-8'))
            
        except:
            break
            
    with lock:
        total_motoristas_online -= 1
    print(f"[DESCONECTADO] {nome_motorista} ({addr})")
    conn.close()

def main():
    global total_motoristas_online, banco_motoristas
    
    #1 - limite de conexões via linha de comando 
    if len(sys.argv) < 2:
        print("Uso: python server.py <limite_conexoes>")
        return
    LIMITE = int(sys.argv[1])
    
    #2 - carrega persistência 
    banco_motoristas = carregar_dados()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"[INICIANDO] Servidor Uber Fase 2 | Limite: {LIMITE} motoristas")

    while True:
        conn, addr = server.accept()
        
        #3 - validação de Limite [cite: 233]
        if total_motoristas_online >= LIMITE:
            conn.sendall("ERRO: Servidor lotado. Tente mais tarde.\n".encode('utf-8'))
            conn.close()
            continue

        #4 - fase de Identificação (O motorista deve enviar o nome primeiro)
        conn.sendall("BEM-VINDO! Digite seu nome para iniciar: ".encode('utf-8'))
        nome = conn.recv(1024).decode('utf-8').strip()

        with lock:
            total_motoristas_online += 1
            if nome not in banco_motoristas:
                banco_motoristas[nome] = {"saldo": 0.0} #novos motoristas começam com zero
                print(f"[NOVO MOTORISTA] {nome} cadastrado.")
            else:
                print(f"[RETORNO] {nome} conectou. Saldo recuperado: R${banco_motoristas[nome]['saldo']:.2f}") [cite: 272]
            
            posicao = total_motoristas_online

        salvar_dados()
        horario = datetime.now().strftime("%H:%M")
        conn.sendall(f"<{horario}>: CONECTADO!! Ola {nome}.\n> ".encode('utf-8')) [cite: 91, 202]

        #5 - threads dedicadas (cada cliente com 2 threads) [cite: 232]
        threading.Thread(target=thread_recebe_comandos, args=(conn, addr, nome, posicao)).start()
        #thread de geração de corridas (exemplo simplificado)
        #threading.Thread(target=thread_gera_corridas, args=(conn,)).start()

if __name__ == "__main__":
    main()
