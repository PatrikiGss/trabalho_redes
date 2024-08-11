import socket
import json

def send_command(command, locate, state=None):
    try:
        message = {
            "command": command,
            "locate": locate
        }
        if state:
            message["state"] = state

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        endereço_servidor = ('127.0.0.1', 5000)
        sock.sendto(json.dumps(message).encode('utf-8'), endereço_servidor)
        data, _ = sock.recvfrom(1024)
        resposta = json.loads(data.decode('utf-8'))
        print(resposta)
    except socket.error as e:
        print(f"Erro de socket: {e}")
    except json.JSONDecodeError:
        print("Erro ao decodificar resposta JSON")
    finally:
        sock.close()


print("GET")#olhando o estado inicial do dispositivo luz sala de reuniao.
send_command("get", "luz_sala_reunioes")

print("SET")#seta um novo estado, "ligado", ou "desligado".
send_command("set", "luz_sala_reunioes", "ligado")

print("GET")# olhando novamente o estado do disposivo apos alteração.
send_command("get", "luz_sala_reunioes")

print("GET all")#retorna todos os dispositivos.
send_command("GET ALL","GET ALL")

