import socket
import json

HOST = '127.0.0.1'  # Endereço IP do servidor
PORT = 50000        # Porta que o servidor está escutando

# Mensagem JSON de exemplo que o cliente vai enviar
# Comandos aceitos pelo servidor: 
# 'ADICIONAR_INFO' add um arquivo a lista. 
# 'LISTAR_INFO' lista os arquivos. 
# 'ALTERAR_ARQUIVO' altera um dado dentro do arquivo
mensagem = {
    "comando": "ADICIONAR_INFO",
    "diretorio": "trabalho_redes-main",
    "arquivo": "dados.json",
    "chave": "arquivos",
    "dados": {"nome": "foto.jpg", "tamanho": 12}
}

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(json.dumps(mensagem).encode('utf-8'))  # Envia a mensagem para o servidor
    resposta = s.recv(1024)                          # Recebe a resposta do servidor
    print('Resposta do servidor:', resposta.decode('utf-8'))
