import socket
import json
import os
    
def listar_informacoes_do_arquivo_json(diretorio, nome_arquivo, chave_lista):
    caminho_arquivo = os.path.join(diretorio, nome_arquivo)
    try:
        with open(caminho_arquivo, 'r') as f:
            conteudo = json.load(f)  # Carrega o conteúdo do arquivo JSON
            
            # Verifica se a chave desejada existe no JSON
            if chave_lista in conteudo:
                lista_info = conteudo[chave_lista]
                return {"status": "sucesso", "dados": lista_info}
            else:
                return {"status": "erro", "mensagem": f"Chave '{chave_lista}' não encontrada no JSON."}
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}
    
# Função para adicionar novas informações a uma lista em um arquivo JSON
def adicionar_informacoes_ao_json(diretorio, nome_arquivo, chave_lista, novos_dados):
    caminho_arquivo = os.path.join(diretorio, nome_arquivo)

    try:
        # Carregar o conteúdo atual do arquivo JSON
        with open(caminho_arquivo, 'r+') as file:
            conteudo = json.load(file)
            
            # Verificar se a chave da lista existe
            if chave_lista in conteudo:
                # Verificar se o valor da chave é uma lista
                if isinstance(conteudo[chave_lista], list):
                    conteudo[chave_lista].append(novos_dados)  # Adicionar novos dados à lista
                else:
                    return {"status": "erro", "mensagem": f"O valor associado a '{chave_lista}' não é uma lista."}
            else:
                return {"status": "erro", "mensagem": f"Chave '{chave_lista}' não encontrada no JSON."}
            
            # Reescrever o arquivo JSON com as novas informações
            file.seek(0)  # Voltar ao início do arquivo
            json.dump(conteudo, file, indent=4)
            file.truncate()  # Garantir que não fique nenhum dado residual
            
        return {"status": "sucesso", "mensagem": "Informações adicionadas com sucesso."}
    
    except Exception as e:
        return {"status": "erro", "mensagem": str(e)}

# Função que processa a solicitação recebida pelo servidor
def processar_requisicao(mensagem):
    try:
        dados = json.loads(mensagem)

        if "comando" in dados:
            if dados["comando"] == "LISTAR_INFO":
                # Exemplo: {"comando": "LISTAR_INFO", "chave": "arquivos"}
                resposta = listar_informacoes_do_arquivo_json(dados["diretorio"], dados["arquivo"], dados["chave"])

            elif dados["comando"] == "ADICIONAR_INFO":
                # Exemplo: {"comando": "ADICIONAR_INFO", "chave": "usuarios", "dados": {"nome": "Pedro", "idade": 22}}
                resposta = adicionar_informacoes_ao_json(dados["diretorio"], dados["arquivo"], dados["chave"], dados["dados"])
            else:
                resposta = {"status": "erro", "mensagem": "Comando não reconhecido."}
        else:
            resposta = {"status": "erro", "mensagem": "Formato de mensagem inválido."}
    except json.JSONDecodeError:
        resposta = {"status": "erro", "mensagem": "Erro ao decodificar JSON."}
    
    return json.dumps(resposta)

# Configurações do servidor
HOST = '127.0.0.1'  # Endereço IP do servidor
PORT = 50000        # Porta que o servidor vai escutar

# Criar o socket TCP
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()

    print(f"Servidor rodando em {HOST}:{PORT}")

    while True:
        conn, addr = s.accept()
        with conn:
            print(f"Conectado por {addr}")
            while True:
                dados = conn.recv(1024)
                if not dados:
                    break
                mensagem_recebida = dados.decode('utf-8')
                resposta = processar_requisicao(mensagem_recebida)
                conn.sendall(resposta.encode('utf-8'))
