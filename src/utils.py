import re
import unicodedata
from decimal import Decimal, ROUND_HALF_UP


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


def dinheiro(valor):
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"R$ {valor:.2f}".replace(".", ",")


def numero_decimal(texto_numero):
    texto_numero = texto_numero.strip().replace("R$", "").replace("r$", "").strip()
    if "," in texto_numero:
        texto_numero = texto_numero.replace(".", "").replace(",", ".")
    return Decimal(texto_numero)


def expandir_lexico_brasileiro(texto_lower):
    mapeamento = {
        r"\bvlr\b": "valor",
        r"\bpgto\b": "pagamento",
        r"\bpagmto\b": "pagamento",
        r"\bparc\b": "parcela",
        r"\bjrs\b": "juros",
        r"\bbol\b": "boleto",
        r"\bboleto\b": "boleto",
        r"\bgrana\b": "dinheiro",
        r"\bdindin\b": "dinheiro",
        r"\bdimdim\b": "dinheiro",
        r"\bmofou\b": "atendimento humano",
        r"\bfazer a boa\b": "formas de pagamento",
        r"\bquebrar o galho\b": "formas de pagamento",
        r"\bta caro\b": "limite de orcamento",
        r"\bmudei de ideia\b": "formas de pagamento",
    }
    for padrao, substituicao in mapeamento.items():
        texto_lower = re.sub(padrao, substituicao, texto_lower)
    return texto_lower
