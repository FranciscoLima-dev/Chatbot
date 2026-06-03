import re
from decimal import Decimal

from .cart import CartItem
from .utils import numero_decimal


NUMEROS_EXTENSO = {
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "tres": 3,
    "três": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
    "dez": 10,
    "onze": 11,
    "doze": 12,
}

CATALOGO_ROUPAS = {
    "camisa": {
        "nome": "Camisa",
        "precos": {"p": Decimal("50"), "m": Decimal("55"), "g": Decimal("60")},
    }
}

CORES_ROUPAS = {
    "preta": "preta",
    "preto": "preta",
    "pretas": "preta",
    "pretos": "preta",
    "azul": "azul",
    "azuis": "azul",
    "verde": "verde",
    "verdes": "verde",
    "rosa": "rosa",
    "rosas": "rosa",
    "roxa": "roxa",
    "roxo": "roxa",
    "roxas": "roxa",
    "roxos": "roxa",
    "lilas": "lilas",
    "lilais": "lilas",
    "amarela": "amarela",
    "amarelo": "amarela",
    "amarelas": "amarela",
    "amarelos": "amarela",
    "vermelha": "vermelha",
    "vermelho": "vermelha",
    "vermelhas": "vermelha",
    "vermelhos": "vermelha",
    "marrom": "marrom",
    "marrons": "marrom",
    "branca": "branca",
    "branco": "branca",
    "brancas": "branca",
    "brancos": "branca",
    "cinza": "cinza",
    "cinzas": "cinza",
    "bege": "bege",
    "bejes": "bege",
}


def quantidade_para_int(texto_qtd):
    if not texto_qtd:
        return 1
    return int(texto_qtd) if texto_qtd.isdigit() else NUMEROS_EXTENSO.get(texto_qtd, 1)


def identificar_tamanho(trecho):
    match = re.search(r"\b(?:tamanho|tam)\s*(p|m|g)\b", trecho)
    if match:
        return match.group(1)
    match = re.search(r"\b(p|m|g)\b", trecho)
    return match.group(1) if match else None


def identificar_cor(trecho):
    for cor_texto, cor_catalogo in CORES_ROUPAS.items():
        if re.search(rf"\b{re.escape(cor_texto)}\b", trecho):
            return cor_catalogo
    return None


def tem_produto_nao_suportado(texto):
    return bool(re.search(r"\b(?:bermudas?|shorts?)\b", texto))


def montar_item_camisa(quantidade, cor=None, tamanho=None, valor_unitario=None):
    if tamanho:
        tamanho = tamanho.lower()
    if valor_unitario is None and tamanho:
        valor_unitario = CATALOGO_ROUPAS["camisa"]["precos"].get(tamanho)
    return CartItem(
        produto="camisa",
        quantidade=quantidade,
        cor=cor,
        tamanho=tamanho,
        valor_unitario=valor_unitario,
    )


def extrair_itens_pedido(texto, permitir_inferir=False):
    itens = []
    itens_incompletos = []
    spans = []
    qtd_regex = r"\d+|" + "|".join(NUMEROS_EXTENSO.keys())
    padrao_produto = re.compile(
        rf"(?<!\w)(?:(?P<qtd>{qtd_regex})\s+)?"
        r"(?P<produto>camisas?)\b"
        rf"(?P<detalhes>[^,;.]*?)(?=(?:\s+e\s+(?:(?:{qtd_regex})\s+)?camisas?\b)|$)"
    )

    for match in padrao_produto.finditer(texto):
        qtd = quantidade_para_int(match.group("qtd"))
        trecho_item = match.group(0)
        detalhes = match.group("detalhes") or ""
        cor = identificar_cor(trecho_item)
        tamanho = identificar_tamanho(detalhes)
        valor_match = re.search(r"(?:de|por|a)\s*(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)", detalhes)
        valor_unitario = numero_decimal(valor_match.group(1)) if valor_match else None
        item = montar_item_camisa(qtd, cor, tamanho, valor_unitario)
        spans.append(match.span())
        if item.valor_unitario is None:
            itens_incompletos.append(item)
        else:
            itens.append(item)

    if itens or itens_incompletos or not permitir_inferir:
        return itens, itens_incompletos, spans

    padrao_inferido = re.compile(
        rf"(?<!\w)(?:(?P<qtd>{qtd_regex})\s+)?"
        r"(?P<detalhes>[a-z0-9\s]{1,45}?)\s+"
        r"(?:de|por|a)\s*(?:r\$\s*)?"
        r"(?P<valor>\d+(?:[.,]\d{1,2})?)"
    )
    for match in padrao_inferido.finditer(texto):
        trecho = match.group(0)
        if re.search(r"\b(?:desconto|juros|parcela|parcelas|credito|pix|boleto|total|soma|somar)\b", trecho):
            continue
        cor = identificar_cor(match.group("detalhes"))
        tamanho = identificar_tamanho(match.group("detalhes"))
        if not (cor or tamanho or re.search(r"\b(?:outra|outro|mais|nova|novo)\b", trecho)):
            continue
        qtd = quantidade_para_int(match.group("qtd"))
        valor_unitario = numero_decimal(match.group("valor"))
        itens.append(montar_item_camisa(qtd, cor, tamanho, valor_unitario))
        spans.append(match.span())
        break

    return itens, itens_incompletos, spans


def extrair_parcelas(texto, limite=12):
    match = re.search(r"(?<!\w)(\d{1,2})\s*(?:x|vezes|parcelas|parcela)(?!\w)", texto)
    if not match:
        match = re.search(r"em\s+(\d{1,2})\s*(?:x|vezes|parcelas|parcela)", texto)
    if not match:
        return None
    parcelas = int(match.group(1))
    return parcelas if 1 <= parcelas <= limite else None


def extrair_percentual(texto, palavras):
    palavras_regex = "|".join(re.escape(p) for p in palavras)
    match = re.search(rf"(?:{palavras_regex})\s*(?:de|do|da)?\s*(\d+(?:[.,]\d+)?)\s*%", texto)
    if match:
        return numero_decimal(match.group(1))
    match = re.search(rf"(\d+(?:[.,]\d+)?)\s*%\s*(?:de\s*)?(?:{palavras_regex})", texto)
    if match:
        return numero_decimal(match.group(1))
    return Decimal("0")


def extrair_valores_soltos(texto, spans_ignorados):
    valores = []
    padrao = re.compile(
        r"(?<![\w%])(?:r\$\s*)?(\d+(?:\.\d{3})*(?:[,.]\d{1,2})?|\d+)"
        r"(?!\s*(?:x|vezes|parcelas|parcela|%))(?!\w)"
    )
    for match in padrao.finditer(texto):
        if any(inicio <= match.start(1) < fim for inicio, fim in spans_ignorados):
            continue
        trecho_anterior = texto[max(0, match.start() - 18):match.start()]
        trecho_posterior = texto[match.end():min(len(texto), match.end() + 25)]
        if re.search(r"(desconto|juros|taxa de juros|parcelas?|vezes)\s*(de)?\s*$", trecho_anterior):
            continue
        if re.search(r"\bcamisas?\s*$", trecho_anterior) or re.match(r"\s+camisas?\b", trecho_posterior):
            continue
        valores.append(numero_decimal(match.group(1)))
    return valores


def eh_comando_limpar_carrinho(texto):
    return bool(re.search(r"\b(?:limpar|esvaziar|zerar|cancelar|cancela)\b.*\b(?:carrinho|pedido|compra)\b", texto))


def eh_comando_resumo_carrinho(texto):
    if texto.strip() in ["pix", "boleto", "reembolso"]:
        return False
    return bool(re.search(
        r"\b(?:carrinho|pedido|total|tudo|quanto fica|quanto deu|somar|soma|fechar|pix|desconto|parcelar|parcelas|credito|dividir|divide)\b",
        texto,
    ))


def eh_pergunta_total_carrinho(texto):
    return bool(re.search(r"\b(?:quanto fica|quanto deu|qual o total|total|tudo|resumo do pedido|pedido|carrinho)\b", texto))


def eh_comando_remover_ultimo(texto):
    return bool(re.search(r"\b(?:remover|remove|tirar|tira|excluir|desfazer)\b.*\b(?:ultimo|ultima|item)\b", texto))


def eh_comando_trocar_ultimo(texto, carrinho_tem_itens):
    tem_verbo_troca = re.search(r"\b(?:troca|trocar|substitui|substituir)\b", texto)
    tem_referencia_ultimo = re.search(r"\b(?:ultimo|ultima|ltima)\b", texto)
    return bool(tem_verbo_troca and (tem_referencia_ultimo or (" por " in texto and carrinho_tem_itens)))


def extrair_atualizacao_ultimo_item(texto):
    qtd_match = re.search(r"\b(?:quantidade|qtd)\b.*?(?:para|por|em)?\s*(\d+)\b", texto)
    if qtd_match:
        return "quantidade", int(qtd_match.group(1))

    valor_match = re.search(
        r"\b(?:valor|preco|preco unitario|unitario)\b.*?(?:para|por|em)?\s*(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)",
        texto,
    )
    if valor_match:
        return "valor", numero_decimal(valor_match.group(1))

    return None, None
