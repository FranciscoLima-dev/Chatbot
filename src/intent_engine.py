from .config import DEFAULT_FALLBACK_RESPONSE
from .utils import expandir_lexico_brasileiro, normalizar


def buscar_resposta(mensagem, intencoes):
    mensagem_norm = expandir_lexico_brasileiro(normalizar(mensagem))

    if mensagem_norm in ["cancelar atendimento", "cancelar o atendimento"]:
        return {
            "tag": "exit",
            "resposta": "Atendimento finalizado. Obrigado por falar com o Financeiro da FashionFlow.",
            "encerrar": True,
        }

    for intencao in intencoes:
        for padrao in intencao["regex_palavras"]:
            if padrao.search(mensagem_norm):
                return intencao

    return {
        "tag": "fallback",
        "resposta": DEFAULT_FALLBACK_RESPONSE,
        "encerrar": False,
    }
