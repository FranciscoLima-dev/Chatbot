import csv
import re

from .config import KNOWLEDGE_BASE_FILE
from .utils import normalizar


def carregar_intencoes(caminho_csv=KNOWLEDGE_BASE_FILE):
    intencoes = []
    with open(caminho_csv, newline="", encoding="utf-8") as arquivo:
        reader = csv.DictReader(arquivo)
        for row in reader:
            palavras_lista = [p.strip() for p in row["palavras"].split(",")]
            regex_compiladas = [
                re.compile(r"(?<!\w)" + re.escape(normalizar(p)) + r"(?!\w)")
                for p in palavras_lista
                if p
            ]
            intencao = {
                "tag": row["tag"],
                "prioridade": int(row["prioridade"]),
                "regex_palavras": regex_compiladas,
                "resposta": row["resposta"],
            }
            if row["pergunta_seguinte"]:
                intencao["pergunta_seguinte"] = row["pergunta_seguinte"]
            if row["encerrar"] == "True":
                intencao["encerrar"] = True
            intencoes.append(intencao)

    return sorted(intencoes, key=lambda item: item["prioridade"])
