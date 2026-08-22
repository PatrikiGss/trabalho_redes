import json
import socket
import struct
import threading
import uuid
from datetime import datetime

GRUPO_PADRAO = "239.255.255.255"
PORTA_PADRAO = 5000
TTL_PADRAO = 1
BUFFER = 65507


def create_socket(group, port, ttl=TTL_PADRAO):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Linux exige SO_REUSEPORT para dois processos escutarem a mesma porta.
    if hasattr(socket, "SO_REUSEPORT"):
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
        except OSError:
            pass

    # Sempre INADDR_ANY: no Windows o bind no endereço do grupo falha.
    sock.bind(("", port))

    mreq = struct.pack("=4sl", socket.inet_aton(group), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    # Sem o LOOP ativo, dois clientes na mesma máquina não se enxergam.
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    return sock


def build_payload(client_id, user, msg_sent):
    date = datetime.now()
    return {
        "id": client_id,
        "date": date.strftime("%d/%m/%Y"),
        "time": date.strftime("%H:%M:%S"),
        "username": user,
        "message": msg_sent,
    }


def send_messages(sock, ip, port, msg_sent, user, client_id):
    data = json.dumps(build_payload(client_id, user, msg_sent))
    print("\tSending message to {}:{} with payload: {}\n".format(ip, port, msg_sent))
    sock.sendto(bytes(data, "utf-8"), (ip, port))


def receive_messages(sock, user, client_id):
    while True:
        try:
            msg_received, client = sock.recvfrom(BUFFER)
        except OSError:
            return  # socket fechado no <exit>

        try:
            msg_received = json.loads(msg_received.decode("utf-8"))
            date = msg_received["date"]
            time = msg_received["time"]
            username = msg_received["username"]
            message = msg_received["message"]
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
            continue  # pacote de outra aplicação no mesmo grupo/porta

        # O próprio datagrama volta pelo loopback do multicast: descarta pelo id.
        # Sem id (cliente antigo) cai no critério antigo, o nome de usuário.
        if msg_received.get("id") == client_id:
            continue
        if "id" not in msg_received and username == user:
            continue

        print("Message received from {}{}:\n\t[{}|{}]: {}\n".format(username, client, date, time, message))


def main():
    start_config = input("\tType start config: ")
    if start_config == "1":
        ip = GRUPO_PADRAO
        port = PORTA_PADRAO
        user = "user1"
    elif start_config == "2":
        ip = GRUPO_PADRAO
        port = PORTA_PADRAO
        user = "user2"
    else:
        ip = str(input("\tType multicast group Ip addres: "))
        port = int(input("\tType server UDP port: "))
        user = str(input("\tType a username: "))

    client_id = uuid.uuid4().hex
    sock = create_socket(ip, port)

    threading.Thread(target=receive_messages, args=(sock, user, client_id), daemon=True).start()

    try:
        while True:
            msg_sent = input().strip()

            if msg_sent == "<exit>":
                print("Exiting...")
                return

            if msg_sent:
                send_messages(sock, ip, port, msg_sent, user, client_id)
    except (EOFError, KeyboardInterrupt):
        print("Exiting...")
    finally:
        sock.close()


if __name__ == "__main__":
    main()


"""
    Criação do Socket:
        AF_INET: Endereços IPV4;
        SOCK_DGRAM: Socket UDP;
        IPPROTO_UDP: Específica que o protocolo de transporte é UDP.
"""
"""
        Socket Config:
            SOL_SOCKET: Definindo configurações ao nivel do socket.
            SO_REUSEADDR: Reutilizar endereço (IP + porta) seja reutilizado, em caso de reincialização
            1: Ativa a opção anterior
"""
"""
        Sock Bind:
            Vinculando a porta ao socket em todas as interfaces ('' = INADDR_ANY).
            O bind é feito no INADDR_ANY e não no endereço do grupo porque o
            Windows recusa o bind direto em endereço multicast.
"""
"""
        mreq: Impacotar o endereço IP e a interface local em um formato binário adequado.
            =4sl: 4s = String de 4 bytes, l = inteiro longo
            inet_aton(ip): Converte enderçeo ip para um formato binário
            INADDR_ANY: qualquer interface de rede disponivel pode ser usada
"""
"""
        MultiCast Group config:
            IPPROTO_IP: Definindo configuração ao nivel do protocolo.
            IP_ADD_MEMBERSHIP: Adiciona o socket em um grupo multicast.
            mreq: endereço empacotado interface e interface local.
            IP_MULTICAST_TTL: quantos roteadores o datagrama pode atravessar (1 = rede local).
            IP_MULTICAST_LOOP: entrega uma cópia do datagrama à própria máquina,
                necessário para vários clientes rodando no mesmo host se enxergarem.
"""
