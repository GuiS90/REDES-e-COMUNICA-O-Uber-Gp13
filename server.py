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
lock = threading.RLock()

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

def thread_recebe_comandos(conn, addr, nome_motorista, posicao_privada, sessao):
    global total_motoristas_online
    
    while True:
        try:
            msg = conn.recv(1024).decode('utf-8')
            if not msg: break
            
            comando = msg.strip()
            resposta_comando = ""

            if comando == ":status":
                with lock:
                    saldo = banco_motoristas[nome_motorista]["saldo"]
                    status_atual = sessao["status"]
                resposta_comando = f"Status: {status_atual.upper()} | Faturamento Total: R${saldo:.2f} | Posição: {posicao_privada}"

            elif comando == ":accept":
                with lock:
                    if sessao["status"] == "livre":
                        sessao["status"] = "em corrida"
                        #credita o valor da ultima corrida gerada pela Thread 2
                        valor = sessao["ultima_corrida_valor"]
                        banco_motoristas[nome_motorista]["saldo"] += valor
                        salvar_dados()
                        resposta_comando = f"Corrida aceita! Valor de R${valor:.2f} foi creditado na sua conta."
                    else:
                        resposta_comando = "Você já está em uma corrida."

            elif comando == ":cancel":
                with lock:
                    if sessao["status"] == "em corrida":
                        #estorna o valor se cancelado
                        banco_motoristas[nome_motorista]["saldo"] -= sessao["ultima_corrida_valor"]
                        sessao["status"] = "livre"
                        sessao["ultima_corrida_valor"] = 0.0
                        salvar_dados()
                        resposta_comando = "Corrida cancelada e valor estornado."
                    else:
                        resposta_comando = "Não há corrida para cancelar."
            elif comando == ":finish":
                with lock:
                    if sessao["status"] == "em corrida":
                        sessao["status"] = "livre"
                        resposta_comando = "Corrida finalizada com sucesso! Estás disponível para novos alertas."
                    else:
                        resposta_comando = "Erro: Não estás em nenhuma corrida ativa para finalizar."
            elif comando == ":quit":
                resposta_comando = "Deslogando... Dados salvos."
                conn.sendall(f"Voce executou: [{comando}]\n{resposta_comando}\n".encode('utf-8'))
                break
            
            else:
                resposta_comando = "Comando não reconhecido."

            #eco de confirmação
            conn.sendall(f"Voce executou: [{comando}]\n{resposta_comando}\n> ".encode('utf-8'))
            
        except:
            break
            
    with lock:
        total_motoristas_online -= 1
    print(f"[DESCONECTADO] {nome_motorista} ({addr})")
    conn.close()

def thread_gera_corridas(conn, sessao):
    #thread 2: gera eventos de corridas para ESTE motorista
    while True:
        time.sleep(15) #espera 15 segundos pra gerar uma corrida
        
        with lock:
            if sessao["status"] == "livre":
                #gerando dados aleatórios da corrida
                distancia_inicio = random.randint(1, 10)
                distancia_corrida = random.randint(5, 30)
                valor = random.uniform(15.0, 45.0)
                
                #salvamos o valor na sessão para que o :accept saiba quanto cobrar
                sessao["ultima_corrida_valor"] = valor
                
                #formatando o alerta assíncrono
                alerta = f"\n[ALERTA UBER] Nova corrida! Distância até o passageiro: {distancia_inicio}km. Distância da viagem: {distancia_corrida}km. Valor: R${valor:.2f}\n> "
                
                try:
                    conn.sendall(alerta.encode('utf-8'))
                except:
                    break #se der erro, o cliente desconectou

def main():
    global total_motoristas_online, banco_motoristas
    
    #1 - carrega persistência 
    banco_motoristas = carregar_dados()

    #2 - pergunta o limite ao iniciar
    print("========================================")
    print("       SISTEMA UBER - SERVIDOR          ")
    print("========================================")
    try:
        LIMITE = int(input("Digite o limite maximo de motoristas: "))
    except ValueError:
        print("Erro: Digite apenas numeros. Usando padrao: 5")
        LIMITE = 5

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(ADDR)
    server.listen()
    print(f"\n[INICIANDO] Servidor Uber Fase 3")
    print(f"[AGUARDANDO] Limite: {LIMITE} motoristas | Endereco: {SERVER}:{PORT}\n")

    while True:
        conn, addr = server.accept()
        
        #3 - validação de Limite
        if total_motoristas_online >= LIMITE:
            conn.sendall("ERRO: Servidor lotado. Tente mais tarde.\n".encode('utf-8'))
            conn.close()
            continue

        #4 - fase de Identificação
        conn.sendall("BEM-VINDO! Digite seu nome para iniciar: ".encode('utf-8'))
        nome = conn.recv(1024).decode('utf-8').strip()

        if not nome:
            nome = f"Motorista_{random.randint(100,999)}"

        with lock:
            total_motoristas_online += 1
            if nome not in banco_motoristas:
                banco_motoristas[nome] = {"saldo": 0.0} 
                print(f"[NOVO MOTORISTA] {nome} cadastrado.")
            else:
                print(f"[RETORNO] {nome} conectou. Saldo recuperado: R${banco_motoristas[nome]['saldo']:.2f}")
            
            posicao = total_motoristas_online

        salvar_dados()
        horario = datetime.now().strftime("%H:%M")
        conn.sendall(f"<{horario}>: CONECTADO!! Ola {nome}.\n> ".encode('utf-8'))

        # --- CORREÇÃO AQUI ---
        # Criamos o estado Deste motorista e passamos para as duas threads dele!
        sessao_motorista = {"status": "livre", "ultima_corrida_valor": 0.0}

        #5 - threads dedicadas (cada cliente com 2 threads ativas)
        threading.Thread(target=thread_recebe_comandos, args=(conn, addr, nome, posicao, sessao_motorista)).start()
        threading.Thread(target=thread_gera_corridas, args=(conn, sessao_motorista)).start()

if __name__ == "__main__":
    main()
