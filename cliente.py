# coding:utf-8
# UNIVERSIDADE FEDERAL DO RIO GRANDE DO NORTE
# DEPARTAMENTO DE ENGENHARIA DE COMPUTACAO E AUTOMACAO
# DISCIPLINA REDES DE COMPUTADORES (DCA0113)
# AUTOR: PROF. CARLOS M D VIEGAS (viegas 'at' dca.ufrn.br)
#
# SCRIPT: Cliente de sockets TCP modificado para enviar texto minusculo ao servidor e aguardar resposta em maiuscula
#

# importacao das bibliotecas
from socket import *
from threading import Thread
from queue import Queue


class Servidor(Thread):
    def __init__(self, socket, nome_fila, priv):
        Thread.__init__(self)
        self.socket = socket
        self.nome_fila = nome_fila
        self.priv = priv

    def run(self):
        # ------------------- ESCUTA SERVER -----------------------
        while True:
            try:
                # Recebe 1º byte do cliente - tamanho mensagem
                tamanho_msg = int.from_bytes(clientSocket.recv(1), byteorder="big")

                if tamanho_msg > 0:
                    # Obtem endereços IP destino e do remetente
                    enderecos = self.socket.recv(8)
                    origem = list(map(int, enderecos[0:4]))
                    destino = list(map(int, enderecos[4:8]))

                    # Obtem nick de destino
                    nick = self.socket.recv(6).decode("utf-8").replace("0", "")

                    # Obtem codigo do comando
                    comando = int.from_bytes(self.socket.recv(1), byteorder="big")

                    # Obem mensagem enviada (tamanho_msg - tamanho cabaçalho [24] bytes)
                    tamanho_msg -= 16
                    if tamanho_msg <= 40:
                        mensagem = self.socket.recv(tamanho_msg).decode("utf-8")

                        # SAIR
                        if comando == 0:  # sair()
                            f = bytes([16, 192, 168, 0, 1, 10, 0, 0, 1])  # Insere n�meros no vetor de bytes
                            f += ":".encode("utf-8") * (6 - len("all")) + "all".encode(
                                "utf-8")  # insere o nick no vetor de bytes, preenchendo com 0 a esqueda para que preencha os 8 octetos

                            f += bytes([11])
                            # print(f)
                            self.socket.send(f)

                            self.socket.close()
                            print("Servidor desconectado. Pressione enter para sair")
                            break

                        # APENAS IMPRIMIR DADOS RECEBIDOS
                        # 2 - falar
                        # 3 - listar
                        # 6 - Requerir novo nick
                        # 8 - confirmar privado
                        elif comando == 2:
                            print(mensagem)

                        elif comando == 9:
                            print(mensagem + " recusou o pedido")
                            self.nome_fila.put("")
                        elif comando == 5:
                            print("Você saiu do privado")
                            self.nome_fila.put("")
                            priv.put(False)
                        elif comando == 4:
                            print("Deseja falar privado com " + mensagem + " ?")
                            self.nome_fila.put(mensagem)
                        elif comando == 8:
                            priv.put(True)
                            print(mensagem)

                    else:
                        mensagem = self.socket.recv(40).decode("utf-8")
                        print(mensagem, end="")

                    # 2 - falar,
                    # 3 - listar,
                    # 4 - requisitar privado,
                    # 1 - entrando,
                    # 5 - sair privado,
                    # 6 - mudar nick
                    # 8 - confirma privado,
                    # 7 - Eliminar cliente
                    # 9 - recusar privado


            # Exceção para se server sair do nada
            except ConnectionResetError:
                break
            # Exceção para se server sair do nada
            except (ConnectionAbortedError, OSError):
                print("Fim do chat")                
                break

try:
    # ---------------------- definicao das variaveis ------------------------
    # Sempre digite em IP
    serverName = "localhost"#'177.89.236.221'
    if serverName != "localhost":
        host = list(map(int, serverName.split(".")))
    else:
        host = [127, 0, 0, 1]

    serverPort = 14000
    clientSocket = socket(AF_INET, SOCK_STREAM)  # criacao do socket TCP
    clientSocket.connect((serverName, serverPort))  # conecta o socket ao servidor
    cliente = gethostbyname(gethostname())

    nome = Queue()
    priv = Queue()

    #--------------Entrando no servidor ----------------------------------
    # Insere números no vetor de bytes
    f = bytes([16] + host + list(map(int, cliente.split("."))))
    # insere o nick no vetor de bytes, preenchendo com 0 a esquerda para que preencha os 6 bytes
    f += ":".encode("utf-8") * (6 - len("all")) + "all".encode("utf-8")
    # insere comando
    f += bytes([1])
    clientSocket.send(f)
    #--------------Entrando no servidor ----------------------------------

    server = Servidor(clientSocket, nome, priv)
    server.start()

    print("Chat iniciado")

    pediu_privado = ""
    privado = False

    #------------- ENVIA PARA SERVER -------------------------------------
    while True:


        sentence = input("> ")

        if not priv.empty():
            privado = priv.get()


        if  server.is_alive():
            if sentence == "sair()":
                comando = 0
                # Insere n�meros no vetor de bytes
                f = bytes([16, 192, 168, 0, 1, 10, 0, 0, 1])
                # insere o nick no vetor de bytes, preenchendo com 0 a esqueda para que preencha os 6 bytes (octetos)
                f += ":".encode("utf-8") * (6 - len("all")) + "all".encode(
                    "utf-8")
                f += bytes([0])
                clientSocket.send(f)

                clientSocket.shutdown(SHUT_RDWR)
                clientSocket.close()
                break

            elif sentence.startswith("nome(") and sentence.endswith(")"):
                #Remove "nome(" e o último caractere ")"
                sentence = sentence[5:]
                sentence = sentence[0:-1] #para retira o ")"

                if len(sentence) <= 6 and len(sentence) > 0 and sentence != "nome()" and ":" not in sentence:
                    comando = 6
                else:
                    print("Nome inválido")
                    continue

            elif sentence == "listar()":
                comando = 3

            elif sentence.startswith("privado(") and sentence.endswith(")"):
                comando = 4
                sentence = sentence[8:]
                sentence = sentence[0:-1]  # para retira o ")"
                pediu_privado = sentence

            elif sentence == "confirmar":
                comando = 8
                sentence = nome.get()
                pediu_privado = sentence
                privado = True

            elif sentence == "negar" and len(pediu_privado) > 0:
                comando = 9
                sentence = pediu_privado
                pediu_privado = ""
                privado = False

            elif sentence == "sair_privado()" and len(pediu_privado) > 0:
                comando = 5
                sentence = pediu_privado
                pediu_privado = ""
                privado = False

            else:
                comando = 2


            sentence = sentence.encode("utf-8")
            f = bytes([len(sentence) + 16, 192, 168, 0, 1, 10, 0, 0, 1])  # Insere n�meros no vetor de bytes

            if not privado:
                f += ":".encode("utf-8") * (6 - len("all")) + "all".encode(
                "utf-8")  # insere o nick no vetor de bytes, preenchendo com 0 a esqueda para que preencha os 8 octetos
            else:
                f += ":".encode("utf-8") * (6 - len(pediu_privado)) + pediu_privado.encode(
                    "utf-8")

            f += bytes([comando]) + sentence

            # print(f)
            clientSocket.send(f)
        else:
            break

      # encerramento o socket do cliente
except ConnectionRefusedError:
    print("Servidor está desconectado")

