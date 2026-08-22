"""Interface gráfica simples (Tkinter) para o chat UDP multicast.

Usa o mesmo socket e o mesmo payload JSON do client_to_client.py, então a
janela e o cliente de terminal conversam entre si no mesmo grupo.

Executar:  python chat_gui.py
"""

import json
import queue
import threading
import tkinter as tk
import uuid
from tkinter import messagebox, scrolledtext, ttk

from client_to_client import (
    BUFFER,
    GRUPO_PADRAO,
    PORTA_PADRAO,
    build_payload,
    create_socket,
)


class ChatApp:
    def __init__(self, root):
        self.root = root
        self.sock = None
        self.client_id = uuid.uuid4().hex
        self.fila = queue.Queue()

        root.title("Chat UDP Multicast")
        root.minsize(560, 420)
        root.columnconfigure(0, weight=1)
        root.rowconfigure(1, weight=1)

        self._build_barra_conexao()
        self._build_area_mensagens()
        self._build_barra_envio()

        root.protocol("WM_DELETE_WINDOW", self.ao_fechar)
        root.after(100, self._consumir_fila)

    # ------------------------------------------------------------------ UI

    def _build_barra_conexao(self):
        barra = ttk.Frame(self.root, padding=8)
        barra.grid(row=0, column=0, sticky="ew")

        ttk.Label(barra, text="Grupo:").grid(row=0, column=0, padx=(0, 4))
        self.var_grupo = tk.StringVar(value=GRUPO_PADRAO)
        self.ent_grupo = ttk.Entry(barra, textvariable=self.var_grupo, width=16)
        self.ent_grupo.grid(row=0, column=1, padx=(0, 10))

        ttk.Label(barra, text="Porta:").grid(row=0, column=2, padx=(0, 4))
        self.var_porta = tk.StringVar(value=str(PORTA_PADRAO))
        self.ent_porta = ttk.Entry(barra, textvariable=self.var_porta, width=7)
        self.ent_porta.grid(row=0, column=3, padx=(0, 10))

        ttk.Label(barra, text="Usuário:").grid(row=0, column=4, padx=(0, 4))
        self.var_user = tk.StringVar(value="user1")
        self.ent_user = ttk.Entry(barra, textvariable=self.var_user, width=14)
        self.ent_user.grid(row=0, column=5, padx=(0, 10))

        self.btn_conectar = ttk.Button(barra, text="Conectar", command=self.alternar_conexao)
        self.btn_conectar.grid(row=0, column=6)

        barra.columnconfigure(7, weight=1)
        self.lbl_status = ttk.Label(barra, text="Desconectado", foreground="#a33")
        self.lbl_status.grid(row=0, column=7, sticky="e")

    def _build_area_mensagens(self):
        self.txt = scrolledtext.ScrolledText(self.root, wrap="word", state="disabled", height=18)
        self.txt.grid(row=1, column=0, sticky="nsew", padx=8)
        self.txt.tag_config("sistema", foreground="#777", font=("TkDefaultFont", 9, "italic"))
        self.txt.tag_config("eu", foreground="#1a6b1a")
        self.txt.tag_config("outro", foreground="#12457a")
        self.txt.tag_config("hora", foreground="#999")

    def _build_barra_envio(self):
        barra = ttk.Frame(self.root, padding=8)
        barra.grid(row=2, column=0, sticky="ew")
        barra.columnconfigure(0, weight=1)

        self.var_msg = tk.StringVar()
        self.ent_msg = ttk.Entry(barra, textvariable=self.var_msg, state="disabled")
        self.ent_msg.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.ent_msg.bind("<Return>", lambda _evento: self.enviar())

        self.btn_enviar = ttk.Button(barra, text="Enviar", command=self.enviar, state="disabled")
        self.btn_enviar.grid(row=0, column=1)

    # ------------------------------------------------------------- conexão

    def alternar_conexao(self):
        if self.sock is None:
            self.conectar()
        else:
            self.desconectar()

    def conectar(self):
        grupo = self.var_grupo.get().strip()
        user = self.var_user.get().strip()
        try:
            porta = int(self.var_porta.get())
        except ValueError:
            messagebox.showerror("Chat", "Porta inválida.")
            return
        if not user:
            messagebox.showerror("Chat", "Informe um nome de usuário.")
            return
        if not self._eh_multicast(grupo):
            messagebox.showerror("Chat", "O endereço precisa ser um grupo multicast (224.0.0.0 a 239.255.255.255).")
            return

        try:
            self.sock = create_socket(grupo, porta)
        except OSError as erro:
            messagebox.showerror("Chat", "Não foi possível abrir o socket:\n{}".format(erro))
            self.sock = None
            return

        self.grupo, self.porta, self.user = grupo, porta, user
        threading.Thread(target=self._receber, args=(self.sock,), daemon=True).start()

        self._alternar_widgets(conectado=True)
        self.lbl_status.config(text="No grupo {}:{}".format(grupo, porta), foreground="#1a6b1a")
        self._escrever("Conectado ao grupo {}:{} como {}.".format(grupo, porta, user), "sistema")
        self.ent_msg.focus_set()

    def desconectar(self):
        sock, self.sock = self.sock, None
        if sock is not None:
            sock.close()  # derruba o recvfrom e encerra a thread de recepção
        self._alternar_widgets(conectado=False)
        self.lbl_status.config(text="Desconectado", foreground="#a33")
        self._escrever("Desconectado.", "sistema")

    def _alternar_widgets(self, conectado):
        estado_conexao = "disabled" if conectado else "normal"
        estado_chat = "normal" if conectado else "disabled"
        for widget in (self.ent_grupo, self.ent_porta, self.ent_user):
            widget.config(state=estado_conexao)
        self.ent_msg.config(state=estado_chat)
        self.btn_enviar.config(state=estado_chat)
        self.btn_conectar.config(text="Desconectar" if conectado else "Conectar")

    @staticmethod
    def _eh_multicast(ip):
        partes = ip.split(".")
        if len(partes) != 4 or not all(p.isdigit() and 0 <= int(p) <= 255 for p in partes):
            return False
        return 224 <= int(partes[0]) <= 239

    # ---------------------------------------------------------------- rede

    def enviar(self):
        texto = self.var_msg.get().strip()
        if not texto or self.sock is None:
            return

        payload = build_payload(self.client_id, self.user, texto)
        try:
            self.sock.sendto(json.dumps(payload).encode("utf-8"), (self.grupo, self.porta))
        except OSError as erro:
            self._escrever("Falha ao enviar: {}".format(erro), "sistema")
            return

        self.var_msg.set("")
        self._escrever_mensagem(payload, "eu")

    def _receber(self, sock):
        """Roda na thread de recepção: só empilha na fila, nunca toca no Tk."""
        while True:
            try:
                dados, _origem = sock.recvfrom(BUFFER)
            except OSError:
                return  # socket fechado ao desconectar

            try:
                msg = json.loads(dados.decode("utf-8"))
                for chave in ("date", "time", "username", "message"):
                    if chave not in msg:
                        raise KeyError(chave)
            except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError):
                continue  # pacote de outra aplicação no mesmo grupo/porta

            # Descarta a cópia do próprio datagrama devolvida pelo loopback.
            if msg.get("id") == self.client_id:
                continue
            if "id" not in msg and msg["username"] == self.user:
                continue

            self.fila.put(msg)

    def _consumir_fila(self):
        """Roda na thread do Tk: tira da fila e desenha."""
        while True:
            try:
                msg = self.fila.get_nowait()
            except queue.Empty:
                break
            self._escrever_mensagem(msg, "outro")
        self.root.after(100, self._consumir_fila)

    # --------------------------------------------------------------- saída

    def _escrever_mensagem(self, msg, tag):
        self.txt.config(state="normal")
        self.txt.insert("end", "[{}] ".format(msg["time"]), "hora")
        self.txt.insert("end", "{}: ".format(msg["username"]), tag)
        self.txt.insert("end", "{}\n".format(msg["message"]))
        self.txt.config(state="disabled")
        self.txt.see("end")

    def _escrever(self, texto, tag):
        self.txt.config(state="normal")
        self.txt.insert("end", "{}\n".format(texto), tag)
        self.txt.config(state="disabled")
        self.txt.see("end")

    def ao_fechar(self):
        if self.sock is not None:
            self.sock.close()
        self.root.destroy()


def main():
    root = tk.Tk()
    ChatApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
