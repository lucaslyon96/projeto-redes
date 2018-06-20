#coding:utf-8
from threading import Thread
from socket import *


class RecebeDados(Thread):
    def __init__(self, socket, num, addr, fila_tarefas):
        Thread.__init__(self)
        self.socket = socket
        self.nick = "chat" + str(num)
        self.addr = addr
        self.fila_tarefas = fila_tarefas

    def run(self):
        # Continua escutando cliente
        while True:
            try:
                # Recebe 1º byte do cliente - tamanho mensagem
                tamanho_msg = int.from_bytes(self.socket.recv(1), byteorder="big")

                if tamanho_msg > 0:
                    # Obtem endereços IP destino e do remetente
                    enderecos = self.socket.recv(8)
                    origem = map(int, enderecos[0:4])
                    destino = map(int, enderecos[4:8])

                    # Obtem nick de destino
                    nick = self.socket.recv(6).decode("utf-8").replace(":", "")

                    # Obtem codigo do comando
                    comando = int.from_bytes(self.socket.recv(1), byteorder="big")

                    # Obem mensagem enviada (tamanho_msg - tamanho cabaçalho [24] bytes)
                    tamanho_msg -= 16
                    mensagem = self.socket.recv(tamanho_msg).decode("utf-8")

                    if comando == 0:                # sair()
                        self.socket.shutdown(SHUT_RDWR)
                        self.socket.close()
                        self.fila_tarefas.put((7, {"origem": origem,
                                                   "addr": self.addr,
                                                   "destino": list(destino),
                                                   "nick_origem": self.nick,
                                                   "nick_destino": nick,
                                                   "socket": self.socket,
                                                   "mensagem":  self.nick + " saiu"}))
                        break

                    # 1 - entrando
                    elif comando == 1:
                        self.fila_tarefas.put((comando, {"origem": list(origem),
                                                         "addr": self.addr,
                                                         "destino": list(destino),
                                                         "nick_origem": self.nick,
                                                         "nick_destino": nick,
                                                         "socket": self.socket,
                                                         "mensagem": mensagem}))

                    # 2 - falar,
                    # 3 - listar,
                    # 4 - requisitar privado,
                    # 5 - sair privado,
                    # 6 - mudar nick
                    # 8 - confirma privado,
                    # 7 - Eliminar cliente
                    # 9 - recusar privado
                    elif comando in range(1, 10):
                        self.fila_tarefas.put((comando, {"origem": list(origem),
                                                         "addr": self.addr,
                                                         "destino": list(destino),
                                                         "nick_destino": nick,
                                                         "socket": self.socket,
                                                         "mensagem": mensagem}))
                    # confirmação mudança de nick
                    elif comando == 10:
                        self.nick = mensagem
                    elif comando == 11:
                        self.socket.shutdown(SHUT_RDWR)
                        self.socket.close()
                        break
                else:
                    self.socket.shutdown(SHUT_RDWR)
                    self.socket.close()

                    #print(str(nick), str(comando), mensagem)
            # Executado se cliente sair do nada
            except ConnectionResetError:
                self.fila_tarefas.put((7, {"origem": self.addr[0],
                                           "addr": self.addr,
                                           "nick_origem": self.nick,
                                           "nick_destino": "all",
                                           "socket": self.socket,
                                           "mensagem": self.nick + " saiu"}))
                break
            # Quando servidor sai
            except ConnectionAbortedError:
                break
            #except OSError:
            #    break

