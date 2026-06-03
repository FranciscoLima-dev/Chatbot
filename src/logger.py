from datetime import datetime

from .config import LOG_FILE


def registrar_log(quem, mensagem, caminho=LOG_FILE):
    hora = datetime.now().strftime("%H:%M:%S")
    with open(caminho, "a", encoding="utf-8") as arquivo:
        arquivo.write(f"[{hora}] {quem}: {mensagem}\n")
