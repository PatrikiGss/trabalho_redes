import socket
import json
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Estado inicial dos dispositivos
device_states = {
    "luz_guarita": "desligado",
    "ar_guarita": "desligado",
    "luz_estacionamento": "desligado",
    "luz_galpao_externo": "desligado",
    "luz_galpao_interno": "desligado",
    "luz_escritorios": "desligado",
    "ar_escritorios": "desligado",
    "luz_sala_reunioes": "desligado",
    "ar_sala_reunioes": "desligado"
    "All"
}

def handle_client(data, address):
    logging.info(f"Recebido de {address}: {data.decode('utf-8')}")
    message = json.loads(data.decode('utf-8'))
    command = message['command']
    locate = message['locate']

    if command == 'get':
        response = {
            "locate": locate,
            "state": device_states.get(locate, "unknown")
        }
    elif command == "GET ALL":
        response = device_states

    elif command == 'set':
        state = message['state']
        device_states[locate] = state
        response = {
            "locate": locate,
            "state": state
        }
    else:
        response = {"error": "Invalid command"}

    sock.sendto(json.dumps(response).encode('utf-8'), address)
    logging.info(f"Enviado para {address}: {json.dumps(response)}")

# Configuração do servidor UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('0.0.0.0', 5000)
sock.bind(server_address)

print("Servidor pronto para receber comandos...")

while True:
    data, address = sock.recvfrom(1024)
    handle_client(data, address)

