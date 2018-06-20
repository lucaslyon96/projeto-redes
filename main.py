####Servidor
from threading import Thread
from queue import Queue
from socket import *
from sys import platform
from Cliente import RecebeDados
from respostas_requisicoes import GerenciadorRequisicoes


class Conexao(Thread):
    def __init__(self, fila_tarefas, server_socket):
        Thread.__init__(self)
        self.fila_tarefas = fila_tarefas
        self.server_socket = server_socket

    def run(self):
        numero_cliente = 0
        while True:
            # Se o try falhar, foi porque o socket foi fechado
            try:
                # Apesar de estar em um loop infinito, o programa bloqueia aqui até receber uma nova conexão
                # como se fosse o cin do c++
                connectionSocket, addr = self.server_socket.accept()  # aceita as conexoes dos clientes
                processo = RecebeDados(connectionSocket, numero_cliente, addr, self.fila_tarefas)
                numero_cliente += 1
                processo.start()
            except OSError:
                print("Servidor finalizado")
                break



fila_tarefas = Queue()

serverPort = 14000  # porta a se conectar
serverSocket = socket(AF_INET, SOCK_STREAM)  # criacao do socket TCP
#serverSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
serverSocket.bind(('', serverPort))  # bind do ip do servidor com a porta
serverSocket.listen(1)  # socket pronto para 'ouvir' conexoes
host = socket.getsockname(serverSocket)
host = list(map(int, host[0].split('.')))
print('Chat Iniciado. Pronto para receber conexões')


gr = GerenciadorRequisicoes([127, 0, 0, 1], fila_tarefas)
gr.start()

conexao = Conexao(fila_tarefas, serverSocket)
conexao.start()

comando = 0
while True:
    comando = input()
    if comando == "sair()":
        fila_tarefas.put((0, {"origem" : host,
                              "nick_origem": "server",
                              "nick_destino": "all"}))

        fila_tarefas.join()

        if platform == "linux":
            serverSocket.shutdown(SHUT_RDWR)

        serverSocket.close()
        break
    elif comando == "listar()":
        fila_tarefas.put((3, {"origem": host,
                              "nick_origem": "server",
                              "nick_destino": "server"}))







