from threading import Thread
from socket import *

class GerenciadorRequisicoes(Thread):
    def __init__(self, host, fila_tarefas):
        Thread.__init__(self)

        #Informações do host
        self.host = host
        self.server_nick = "server"
        self.fila_tarefas = fila_tarefas

        # Informções dos clientes
        self.addr_clientes = {}     # addr : 0 - socket, 1 - ip, 2 - nick, 3 - privado
        self.privados = {}          # nick_origem : addr_destino

    def run(self):
        Thread.__init__(self)
        while True:
            # https://docs.python.org/3/library/queue.html#module-queue
            # Bloqueia Thread até algo aparecer na fila
            (comando, args) = self.fila_tarefas.get(block=True, timeout=None)

            # Modificar nick
            if comando == 6:
                todos_nicks = []
                for value in self.addr_clientes.values():
                    todos_nicks.append(value[2])

                # Se o nick não for repetido
                if args["mensagem"] not in todos_nicks:
                    # Muda o nick contido em addr_cliente
                    nick_antigo = self.addr_clientes[args["addr"]][2]
                    self.addr_clientes[args["addr"]][2] = args["mensagem"]

                    # Elimina nick antigo da lista de privados e adiciona o novo
                    addr = self.privados.pop(nick_antigo, None)
                    self.privados[args["mensagem"]] = addr

                    mensagem_geral = nick_antigo + " agora é " + args["mensagem"]
                    mensagem_cliente = mensagem_geral

                    # Manda mensagem para todos informando a mudança
                    self.mensagem_todos(mensagem_geral, args["mensagem"], False, 2)
                    print(mensagem_geral)
                else:
                    mensagem_cliente = "Falha: " + args["mensagem"] + " já está sendo usado"

                # Manda a resposta da requisição para o cliente que pediu
                resposta = Resposta(self.addr_clientes[args["addr"]][0],
                                    2,
                                    mensagem_cliente,
                                    self.host,
                                    self.addr_clientes[args["addr"]][1],
                                    self.addr_clientes[args["addr"]][2])
                resposta.start()
                self.fila_tarefas.task_done()
            # Listar()
            elif comando == 3:
                # Texto que contem a lista
                lista = ""
                # Percorre o dicionario
                for chave, valor in self.addr_clientes.items():
                    # se for privado, coloca (privado) depois do nome
                    if valor[3]:
                        lista += str(chave[0]) + ":" + str(chave[1]) + " - " + valor[2] + " (Privado)\n"
                    else:
                        lista += str(chave[0]) + ":" + str(chave[1]) + " - " + valor[2] + "\n"

                # Se foi o server que pediu, só imprime o resultado
                if args["nick_destino"] == self.server_nick:
                    print(lista)
                else:
                    resposta = Resposta(args["socket"],
                                        2,
                                        lista,
                                        self.host,
                                        args["destino"],
                                        self.server_nick)
                    resposta.start()

                self.fila_tarefas.task_done()
            # Adicionar cliente
            elif comando == 1:
                # Adiciona nova entrada em addr_clientes e em nick_addr
                lista = [args["socket"], args["origem"], args["nick_origem"], False]
                self.addr_clientes[args["addr"]] = lista
                mensagem = args["nick_origem"] + " entrou"
                mensagem_cliente = "Seu nick é: " + args["nick_origem"]

                print(mensagem)
                self.mensagem_todos(mensagem, args["nick_origem"], False, 2)

                resposta = Resposta(self.addr_clientes[args["addr"]][0],
                                    2,
                                    mensagem_cliente,
                                    self.host,
                                    self.addr_clientes[args["addr"]][1],
                                    self.addr_clientes[args["addr"]][2])
                resposta.start()

                self.fila_tarefas.task_done()

            elif comando == 4:
                # Verifica se o destino está em privado com outra pessoa
                if args["mensagem"] not in self.privados.keys():
                    self.privados[args["mensagem"]] = args["addr"]

                    # Procura socket do destino e manda mensagem só para quem pediu
                    for key, i in self.addr_clientes.items():
                        if i[2] == args["mensagem"]:
                            self.privados[self.addr_clientes[args["addr"]][2]] = key
                            resposta = Resposta(i[0],
                                                4,
                                                self.addr_clientes[args["addr"]][2],
                                                self.host,
                                                i[1],
                                                i[2])
                            resposta.start()
                            break

                self.fila_tarefas.task_done()

            elif comando == 2:
                nick_origem = self.addr_clientes[args["addr"]][2]

                if args["nick_destino"] == "all":
                    self.mensagem_todos(args["mensagem"], nick_origem, False, 2)
                    print(nick_origem + " escreveu: " + args["mensagem"])

                elif args["addr"] == self.privados[args["nick_destino"]]:
                    resposta = Resposta(self.addr_clientes[self.privados[nick_origem]][0],
                                        2,
                                        args["mensagem"],
                                        self.host,
                                        self.addr_clientes[self.privados[args["nick_destino"]]][1],
                                        args["nick_destino"])
                    resposta.start()

                self.fila_tarefas.task_done()

            elif comando == 8:
                for key, i in self.privados.items():
                    if i == args["addr"]:
                        resposta = Resposta(args["socket"],
                                            8,
                                            "Conversa privada com: " + key,
                                            self.host,
                                            list(map(int, i[0].split("."))),
                                            args["nick_destino"])
                        resposta.start()
                        break


                # Mensagem para quem enviou
                addr_enviou = self.privados[self.addr_clientes[args["addr"]][2]]
                socket = self.addr_clientes[addr_enviou][0]
                resposta = Resposta(socket,
                                    8,
                                    "Conversa privada com: " + self.addr_clientes[args["addr"]][2],
                                    self.host,
                                    self.addr_clientes[addr_enviou][1],
                                    self.addr_clientes[addr_enviou][2])
                resposta.start()

                # Define em true que estão falndo em privado
                for chave, valor in self.addr_clientes.items():
                    if chave == addr_enviou or chave == args["addr"]:
                        valor[3] = True


                self.fila_tarefas.task_done()
            elif comando == 0:
                for i in self.addr_clientes.values():
                    resposta = Resposta(i[0],
                                        0,
                                        "sair()",
                                        self.host,
                                        i[1],
                                        i[2])
                    resposta.start()
                    resposta.join()

                self.addr_clientes.clear()
                self.privados.clear()
                self.fila_tarefas.task_done()
                break
            elif comando == 7:
                nick_origem = self.addr_clientes[args["addr"]][2]
                self.addr_clientes.pop(args["addr"])

                if nick_origem in self.privados.keys():
                    self.privados.pop(nick_origem)

                mensagem = nick_origem + " saiu"
                # Manda mensagem para todos que um cliente saiu
                for i in self.addr_clientes.values():
                    resposta = Resposta(i[0],
                                        2,
                                        mensagem,
                                        self.host,
                                        i[1],
                                        i[2])
                    resposta.start()

                print(mensagem)
                
                self.fila_tarefas.task_done()

            elif comando == 9:
                addr_enviou = self.privados.pop(args["mensagem"])

                for chave, lista in self.addr_clientes.items():
                    if chave == addr_enviou:
                        self.privados.pop(lista[2])
                        resposta = Resposta(lista[0],
                                            9,
                                            args["mensagem"],
                                            self.host,
                                            lista[1],
                                            lista[2])
                        resposta.start()
                        break

                self.fila_tarefas.task_done()

            elif comando == 5:
                nick_origem = self.addr_clientes[args["addr"]][2]
                addr_destino = self.privados.pop(nick_origem)

                addr_origem = ""

                for chave, valor in self.addr_clientes.items():
                    if chave == addr_destino:
                        addr_origem = self.privados.pop(valor[2])
                        resposta = Resposta(valor[0],
                                            5,
                                            args["mensagem"],
                                            self.host,
                                            valor[1],
                                            valor[2])
                        resposta.start()
                        break

                resposta = Resposta(args["socket"],
                                    5,
                                    args["mensagem"],
                                    self.host,
                                    self.addr_clientes[addr_origem][1],
                                    nick_origem)
                resposta.start()

                for chave, valor in self.addr_clientes.items():
                    if chave == addr_destino or chave == args["addr"]:
                        valor[3] = False

                self.fila_tarefas.task_done()

    def mensagem_todos(self, msg, nick_origem, para_todos, comando):
        for i in self.addr_clientes.values():
            # Se não estiver em conversa privada e se não for ele mesmo, manda mensagem global
            if not i[3]:
                if para_todos or i[2] != nick_origem:
                    resposta = Resposta(i[0],
                                        comando,
                                        msg,
                                        self.host,
                                        i[1],
                                        i[2])
                    resposta.start()

class Resposta(Thread):
    def __init__(self, socket, comando, mensagem, origem, destino, nick):
        Thread.__init__(self)
        self.comando = comando
        self.mensagem = mensagem
        self.origem = origem
        self.destino = destino
        self.nick_destino = nick
        self.socket = socket

    def run(self):
        mensagem = self.mensagem.encode("utf-8")
        tamanho_mensagem = len(mensagem)

        endereco = bytes(self.origem) + bytes(self.destino)  # Insere números no vetor de bytes
        nick = ":".encode("utf-8") * (6 - len(self.nick_destino)) + self.nick_destino.encode("utf-8")
        comando = bytes([self.comando])

        if tamanho_mensagem <= 40:
            tamanho_msg = bytes([tamanho_mensagem + 16])
            msg = tamanho_msg + endereco + nick + comando + mensagem
            self.socket.send(msg)
        # Se o tamanho da mensagem for maior que 40, manda em uma serie de várias mensagens
        else:
            i = 0
            while tamanho_mensagem > 0:
                tamanho_msg = bytes([tamanho_mensagem + 16])
                msg = tamanho_msg + endereco + nick + comando + mensagem[i:40 + i]
                self.socket.send(msg)
                tamanho_mensagem -= 40
                i += 40

