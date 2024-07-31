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
        server_address = ('127.0.0.1', 5000)  # Use o endereço IP local para teste
        sock.sendto(json.dumps(message).encode('utf-8'), server_address)
        data, _ = sock.recvfrom(1024)
        response = json.loads(data.decode('utf-8'))
        print(response)
    except socket.error as e:
        print(f"Erro de socket: {e}")
    except json.JSONDecodeError:
        print("Erro ao decodificar resposta JSON")
    finally:
        sock.close()

# Exemplo de uso
print("Teste GET")
send_command("get", "luz_sala_reunioes")

print("Teste SET")
send_command("set", "luz_sala_reunioes", "ligado")

print("Teste GET novamente")
send_command("get", "luz_sala_reunioes")

print(" teste GET all")
send_command("GET ALL","GET ALL")

