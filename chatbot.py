import re
import time
import sys
import csv
import unicodedata
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# ─────────────────────────────────────────────────────────────
#  CÓDIGOS DE CORES E ESTILIZAÇÃO UI/UX (ANSI)
# ─────────────────────────────────────────────────────────────
RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"

# ─────────────────────────────────────────────────────────────
#  CARREGAMENTO E VALIDAÇÃO DA BASE DE CONHECIMENTO
# ─────────────────────────────────────────────────────────────


def carregar_intencoes(caminho_csv="base_conhecimento.csv"):
    intencoes = []
    with open(caminho_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            palavras_lista = [p.strip() for p in row["palavras"].split(",")]

            # Compilação robusta de regex de palavras-chave
            regex_compiladas = [
                re.compile(r'(?<!\w)' + re.escape(normalizar(p)) + r'(?!\w)')
                for p in palavras_lista if p
            ]

            intencao = {
                "tag":           row["tag"],
                "prioridade":    int(row["prioridade"]),
                "regex_palavras": regex_compiladas,
                "resposta":      row["resposta"],
            }
            if row["pergunta_seguinte"]:
                intencao["pergunta_seguinte"] = row["pergunta_seguinte"]
            if row["encerrar"] == "True":
                intencao["encerrar"] = True

            intencoes.append(intencao)

    return sorted(intencoes, key=lambda x: x["prioridade"])

# ─────────────────────────────────────────────────────────────
#  NORMALIZAÇÃO ROBUSTA E EXPANSÃO DE GÍRIAS/ABREVIAÇÕES
# ─────────────────────────────────────────────────────────────


def normalizar(texto):
    if not texto:
        return ""
    texto = texto.lower()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return texto


def expandir_lexico_brasileiro(texto_lower):
    """ Mapeia variações de gírias econômicas e abreviações financeiras do Brasil """
    mapeamento = {
        r'\bvlr\b': 'valor',
        r'\bpgto\b': 'pagamento',
        r'\bpagmto\b': 'pagamento',
        r'\bparc\b': 'parcela',
        r'\bjrs\b': 'juros',
        r'\bbol\b': 'boleto',
        r'\bboleto\b': 'boleto',
        r'\bgrana\b': 'dinheiro',
        r'\bdindin\b': 'dinheiro',
        r'\bdimdim\b': 'dinheiro',
        r'\bmofou\b': 'atendimento humano',
        r'\bfazer a boa\b': 'formas de pagamento',
        r'\bquebrar o galho\b': 'formas de pagamento',
        r'\bta caro\b': 'limite de orcamento',
        r'\bmudei de ideia\b': 'formas de pagamento',
    }
    for padrao, substituicao in mapeamento.items():
        texto_lower = re.sub(padrao, substituicao, texto_lower)
    return texto_lower

# ─────────────────────────────────────────────────────────────
#  LOGS, EXIBIÇÃO E HISTÓRICO COM FORMATO VISUAL MODERNIZADO
# ─────────────────────────────────────────────────────────────


LOG_FILE = "log_atendimento.txt"


def registrar_log(quem, mensagem):
    hora = datetime.now().strftime("%H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{hora}] {quem}: {mensagem}\n")


def bot_falar(texto, efeito_digitacao=True):
    time.sleep(0.4)
    registrar_log("Bot", texto)
    historico_conversa.append({"quem": "bot", "msg": texto})
    historico_recente.append(texto)

    # Identificadores visuais para melhorar legibilidade de alertas e moedas
    texto_colorido = texto.replace("R$", f"{GREEN}{BOLD}R${RESET}{GREEN}")

    sys.stdout.write(f"{GREEN}{BOLD}Bot: {RESET}{GREEN}")
    sys.stdout.flush()
    if efeito_digitacao:
        for caractere in texto_colorido:
            sys.stdout.write(caractere)
            sys.stdout.flush()
            time.sleep(0.008)
        print(f"{RESET}")
    else:
        print(f"{texto_colorido}{RESET}")

# ─────────────────────────────────────────────────────────────
#  ENGINE MATEMÁTICO E ORÇAMENTÁRIO
# ─────────────────────────────────────────────────────────────


NUMEROS_EXTENSO = {
    "um": 1, "uma": 1, "dois": 2, "duas": 2, "tres": 3, "três": 3,
    "quatro": 4, "cinco": 5, "seis": 6, "sete": 7, "oito": 8,
    "nove": 9, "dez": 10, "onze": 11, "doze": 12
}

CATALOGO_ROUPAS = {
    "camisa": {
        "nome": "Camisa",
        "precos": {"p": Decimal("50"), "m": Decimal("55"), "g": Decimal("60")},
    },
}

CORES_ROUPAS = {
    "preta": "preta", "preto": "preta", "pretas": "preta", "pretos": "preta",
    "azul": "azul", "azuis": "azul",
    "verde": "verde", "verdes": "verde",
    "rosa": "rosa", "rosas": "rosa",
    "roxa": "roxa", "roxo": "roxa", "roxas": "roxa", "roxos": "roxa",
    "lilas": "lilas", "lilais": "lilas",
    "amarela": "amarela", "amarelo": "amarela", "amarelas": "amarela", "amarelos": "amarela",
    "vermelha": "vermelha", "vermelho": "vermelha", "vermelhas": "vermelha", "vermelhos": "vermelha",
    "marrom": "marrom", "marrons": "marrom",
    "branca": "branca", "branco": "branca", "brancas": "branca", "brancos": "branca",
    "cinza": "cinza", "cinzas": "cinza",
    "bege": "bege", "bejes": "bege",
}


def dinheiro(valor):
    valor = Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"R$ {valor:.2f}".replace(".", ",")


def numero_decimal(texto_numero):
    texto_numero = texto_numero.strip().replace("R$", "").replace("r$", "").strip()

    if "," in texto_numero:
        texto_numero = texto_numero.replace(".", "").replace(",", ".")

    return Decimal(texto_numero)


def extrair_percentual(texto, palavras):
    palavras_regex = "|".join(re.escape(p) for p in palavras)
    match = re.search(
        rf'(?:{palavras_regex})\s*(?:de|do|da)?\s*(\d+(?:[.,]\d+)?)\s*%',
        texto
    )
    if match:
        return numero_decimal(match.group(1))

    match = re.search(
        rf'(\d+(?:[.,]\d+)?)\s*%\s*(?:de\s*)?(?:{palavras_regex})',
        texto
    )
    if match:
        return numero_decimal(match.group(1))

    return Decimal("0")


def extrair_parcelas(texto):
    match = re.search(r'(?<!\w)(\d{1,2})\s*(?:x|vezes|parcelas|parcela)(?!\w)', texto)
    if not match:
        match = re.search(r'em\s+(\d{1,2})\s*(?:x|vezes|parcelas|parcela)', texto)

    if not match:
        return None

    parcelas = int(match.group(1))
    if 1 <= parcelas <= 24:
        return parcelas

    return None


def identificar_produto_catalogo(texto_produto):
    if re.search(r'\bcamisas?\b', texto_produto):
        return "camisa"
    return None


def identificar_tamanho(trecho):
    match = re.search(r'\b(?:tamanho|tam)\s*(p|m|g)\b', trecho)
    if match:
        return match.group(1)

    match = re.search(r'\b(p|m|g)\b', trecho)
    if match:
        return match.group(1)

    return None


def identificar_cor(trecho):
    for cor_texto, cor_catalogo in CORES_ROUPAS.items():
        if re.search(rf'\b{re.escape(cor_texto)}\b', trecho):
            return cor_catalogo
    return None


def montar_nome_catalogo(produto, tamanho, cor):
    nome = f"{CATALOGO_ROUPAS[produto]['nome']} tamanho {tamanho.upper()}"
    if cor:
        nome += f" {cor}"
    return nome


def tem_produto_nao_suportado(texto):
    return bool(re.search(r'\b(?:bermudas?|shorts?)\b', texto))


def resposta_produto_nao_suportado():
    return (
        "No momento a FashionFlow trabalha apenas com camisas. "
        "Posso calcular seu pedido de camisas se voce informar quantidade, cor e valor unitario ou tamanho."
    )


def extrair_itens_catalogo(texto):
    itens = []
    itens_sem_tamanho = []
    qtd_regex = r'\d+|' + "|".join(NUMEROS_EXTENSO.keys())
    padrao = re.compile(
        rf'(?:(?P<qtd>{qtd_regex})\s+)?'
        r'(?P<produto>camisas?)\b'
    )

    matches = list(padrao.finditer(texto))
    for indice, match in enumerate(matches):
        produto = identificar_produto_catalogo(match.group("produto"))
        if not produto:
            continue

        trecho_depois = texto[match.end():min(len(texto), match.end() + 20)]
        if re.match(r'\s*(?:de|por|a)\s*(?:r\$\s*)?\d', trecho_depois):
            continue

        qtd_texto = match.group("qtd")
        quantidade = 1
        if qtd_texto:
            quantidade = int(qtd_texto) if qtd_texto.isdigit() else NUMEROS_EXTENSO[qtd_texto]

        proximo_inicio = matches[indice + 1].start() if indice + 1 < len(matches) else min(len(texto), match.end() + 45)
        trecho_contexto = texto[match.start():proximo_inicio]
        tamanho = identificar_tamanho(trecho_contexto)
        cor = identificar_cor(trecho_contexto)

        if not tamanho:
            itens_sem_tamanho.append(CATALOGO_ROUPAS[produto]["nome"])
            continue

        valor_unitario = CATALOGO_ROUPAS[produto]["precos"][tamanho]
        nome = montar_nome_catalogo(produto, tamanho, cor)
        itens.append({
            "quantidade": quantidade,
            "nome": nome,
            "valor_unitario": valor_unitario,
            "subtotal": valor_unitario * quantidade,
            "span": match.span(),
        })

    return itens, itens_sem_tamanho


def extrair_itens_com_quantidade(texto):
    itens = []
    qtd_regex = r'\d+|' + "|".join(NUMEROS_EXTENSO.keys())
    padrao = re.compile(
        rf'(?<!\w)(?P<qtd>{qtd_regex})\s+'
        r'(?P<item>camisas?(?:\s+[a-z0-9]+){0,6})\s+'
        r'(?:de|por|a)\s*(?:r\$\s*)?'
        r'(?P<valor>\d+(?:[.,]\d{1,2})?)'
    )

    for match in padrao.finditer(texto):
        qtd_texto = match.group("qtd")
        trecho_anterior = texto[max(0, match.start("qtd") - 8):match.start("qtd")]
        if re.search(r'(?:de|por|r\$)\s*$', trecho_anterior):
            continue

        qtd = int(qtd_texto) if qtd_texto.isdigit() else NUMEROS_EXTENSO[qtd_texto]
        nome = " ".join(match.group("item").split())
        if re.search(r'\b(?:desconto|juros|parcela|parcelas|somando|com|em)\b', nome):
            continue

        valor_unitario = numero_decimal(match.group("valor"))
        cor = identificar_cor(nome)
        tamanho = identificar_tamanho(nome)
        nome_item = "Camisa"
        if cor:
            nome_item += f" {cor}"
        if tamanho:
            nome_item += f" tamanho {tamanho.upper()}"
        itens.append({
            "quantidade": qtd,
            "produto": "camisa",
            "nome": nome_item,
            "cor": cor,
            "tamanho": tamanho,
            "valor_unitario": valor_unitario,
            "subtotal": valor_unitario * qtd,
            "span": match.span(),
        })

    return itens


def extrair_valores_soltos(texto, spans_ignorados):
    valores = []
    padrao = re.compile(r'(?<![\w%])(?:r\$\s*)?(\d+(?:\.\d{3})*(?:[,.]\d{1,2})?|\d+)(?!\s*(?:x|vezes|parcelas|parcela|%))(?!\w)')

    for match in padrao.finditer(texto):
        if any(inicio <= match.start(1) < fim for inicio, fim in spans_ignorados):
            continue

        trecho_anterior = texto[max(0, match.start() - 18):match.start()]
        trecho_posterior = texto[match.end():min(len(texto), match.end() + 25)]
        if re.search(r'(desconto|juros|taxa de juros|parcelas?|vezes)\s*(de)?\s*$', trecho_anterior):
            continue
        if re.search(r'\bcamisas?\s*$', trecho_anterior) or re.match(r'\s+camisas?\b', trecho_posterior):
            continue

        valores.append(numero_decimal(match.group(1)))

    return valores


def montar_resposta_tamanho_faltando(itens_sem_tamanho):
    produtos = ", ".join(sorted(set(itens_sem_tamanho)))
    return (
        f"Encontrei {produtos} no catalogo, mas preciso do valor unitario ou do tamanho para calcular. "
        "Temos camisas P, M e G: P R$ 50,00, M R$ 55,00 e G R$ 60,00."
    )


def montar_resposta_calculo(itens, valores_soltos, desconto, parcelas, juros_mensal):
    linhas = [f"\n{CYAN}Resumo do calculo financeiro FashionFlow:{RESET}"]

    subtotal = Decimal("0")
    if itens:
        linhas.append("Itens identificados:")
        for item in itens:
            subtotal += item["subtotal"]
            linhas.append(
                f"- {item['quantidade']}x {item['nome']} de {dinheiro(item['valor_unitario'])} = {dinheiro(item['subtotal'])}"
            )

    if valores_soltos:
        if itens:
            linhas.append("Valores adicionais:")
        else:
            linhas.append("Valores somados:")

        for indice, valor in enumerate(valores_soltos, start=1):
            subtotal += valor
            linhas.append(f"- Valor {indice}: {dinheiro(valor)}")

    if subtotal <= 0:
        return None

    linhas.append(f"Subtotal: {dinheiro(subtotal)}")

    total = subtotal
    if desconto > 0:
        valor_desconto = (subtotal * desconto / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        total -= valor_desconto
        linhas.append(f"Desconto aplicado ({desconto}%): -{dinheiro(valor_desconto)}")
        linhas.append(f"Total com desconto: {dinheiro(total)}")
    else:
        linhas.append(f"Total: {dinheiro(total)}")

    pix = (total * Decimal("0.95")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    linhas.append(f"No Pix com 5% de desconto: {dinheiro(pix)}")

    if parcelas:
        if juros_mensal > 0:
            total_credito = (total * ((Decimal("1") + juros_mensal / Decimal("100")) ** parcelas)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            parcela = (total_credito / parcelas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            linhas.append(
                f"Credito em {parcelas}x com juros de {juros_mensal}% ao mes: {parcelas}x de {dinheiro(parcela)}"
            )
            linhas.append(f"Total no credito: {dinheiro(total_credito)}")
        else:
            parcela = (total / parcelas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            linhas.append(f"Credito em {parcelas}x sem juros: {parcelas}x de {dinheiro(parcela)}")
    else:
        parcela_12x = (total / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        linhas.append(f"Credito: ate 12x sem juros de {dinheiro(parcela_12x)}")

    return "\n".join(linhas)


def processar_calculo_financeiro(entrada_usuario, entrada_lower):
    """
    Intercepta consultas com valores ou produtos do catalogo, processa soma,
    desconto e simulacao de credito.
    """
    texto = entrada_lower

    palavras_chave_calculo = [
        "quanto fica", "qual valor total", "quanto vou pagar", "total somando",
        "somar", "soma", "calcular", "calcula", "orcamento", "orçamento",
        "custa", "valor total", "preco", "preço", "desconto", "parcelar",
        "parcelas", "credito", "crédito", "juros"
    ]

    if texto.strip() in MENU_FINANCEIRO:
        return None

    itens_catalogo, itens_sem_tamanho = extrair_itens_catalogo(texto)
    tem_produto_catalogo = bool(itens_catalogo or itens_sem_tamanho)

    if not any(c.isdigit() for c in texto) and not tem_produto_catalogo:
        return None

    if itens_sem_tamanho and not itens_catalogo:
        return {
            "resposta": montar_resposta_tamanho_faltando(itens_sem_tamanho),
            "tag": "calculo_concluido",
            "pergunta_seguinte": ""
        }

    itens = itens_catalogo + extrair_itens_com_quantidade(texto)
    spans_itens = [item["span"] for item in itens]
    valores_soltos = extrair_valores_soltos(texto, spans_itens)
    tem_intencao_calculo = any(k in texto for k in palavras_chave_calculo)
    tem_dois_ou_mais_valores = len(itens) + len(valores_soltos) >= 2

    if not (tem_intencao_calculo or itens or tem_dois_ou_mais_valores or tem_produto_catalogo):
        return None

    desconto = extrair_percentual(texto, ["desconto", "cupom", "promocao", "promoção"])
    juros_mensal = extrair_percentual(texto, ["juros", "taxa"])
    parcelas = extrair_parcelas(texto)

    resposta = montar_resposta_calculo(
        itens, valores_soltos, desconto, parcelas, juros_mensal
    )
    if not resposta:
        return None

    return {
        "resposta": resposta,
        "tag": "calculo_concluido",
        "pergunta_seguinte": "Deseja seguir com Pix ou Cartao? (s/n)"
    }

# ─────────────────────────────────────────────────────────────
#  MECANISMO DE BUSCA E ENTIDADES
# ─────────────────────────────────────────────────────────────


# Motor revisado: carrinho em memoria e calculo focado em camisas.
def quantidade_para_int(texto_qtd):
    if not texto_qtd:
        return 1
    return int(texto_qtd) if texto_qtd.isdigit() else NUMEROS_EXTENSO.get(texto_qtd, 1)


def nome_item_carrinho(item):
    partes = ["Camisa"]
    if item.get("cor"):
        partes.append(item["cor"])
    if item.get("tamanho"):
        partes.append(f"tamanho {item['tamanho'].upper()}")
    return " ".join(partes)


def atualizar_subtotal_item(item):
    if item.get("valor_unitario") is None:
        item["subtotal"] = Decimal("0")
    else:
        item["subtotal"] = item["valor_unitario"] * item["quantidade"]


def montar_item_camisa(quantidade, cor=None, tamanho=None, valor_unitario=None, span=None):
    if tamanho:
        tamanho = tamanho.lower()
    if valor_unitario is None and tamanho:
        valor_unitario = CATALOGO_ROUPAS["camisa"]["precos"].get(tamanho)

    item = {
        "produto": "camisa",
        "quantidade": quantidade,
        "cor": cor,
        "tamanho": tamanho,
        "valor_unitario": valor_unitario,
        "subtotal": Decimal("0"),
        "span": span,
    }
    atualizar_subtotal_item(item)
    return item


def item_tem_preco(item):
    return item.get("valor_unitario") is not None


def montar_resposta_item_incompleto(itens_incompletos):
    total_qtd = sum(item["quantidade"] for item in itens_incompletos)
    produto = "camisa" if total_qtd == 1 else "camisas"
    return (
        f"Encontrei {total_qtd} {produto}, mas preciso do valor unitario ou do tamanho antes de calcular. "
        "Voce pode dizer, por exemplo: 'sao 16 camisas de 150' ou '16 camisas tamanho M'."
    )


def montar_resumo_pedido(itens=None, parcelas=None):
    itens = carrinho if itens is None else itens
    itens_com_preco = [item for item in itens if item_tem_preco(item)]
    if not itens_com_preco:
        return "Seu carrinho está vazio no momento. Me diga quais camisas deseja adicionar para eu calcular o total."

    linhas = [f"\n{CYAN}Resumo do pedido FashionFlow:{RESET}"]
    subtotal = Decimal("0")
    for item in itens_com_preco:
        subtotal += item["subtotal"]
        linhas.append(
            f"- {item['quantidade']}x {nome_item_carrinho(item)} de {dinheiro(item['valor_unitario'])} = {dinheiro(item['subtotal'])}"
        )

    pix = (subtotal * Decimal("0.95")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    parcela_12x = (subtotal / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    linhas.append("")
    linhas.append(f"Subtotal: {dinheiro(subtotal)}")
    if parcelas:
        parcela_escolhida = (subtotal / Decimal(parcelas)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        linhas.append(f"Crédito em {parcelas}x sem juros: {parcelas}x de {dinheiro(parcela_escolhida)}")
        linhas.append(f"Pix com 5% de desconto: {dinheiro(pix)}")
    else:
        linhas.append(f"Pix com 5% de desconto: {dinheiro(pix)}")
        linhas.append(f"Crédito: ate 12x sem juros de {dinheiro(parcela_12x)}")
    return "\n".join(linhas)


def montar_resposta_calculo(itens, valores_soltos, desconto, parcelas, juros_mensal):
    linhas = [f"\n{CYAN}Resumo do pedido FashionFlow:{RESET}"]

    subtotal = Decimal("0")
    if itens:
        linhas.append("Itens identificados:")
        for item in itens:
            subtotal += item["subtotal"]
            linhas.append(
                f"- {item['quantidade']}x {nome_item_carrinho(item)} de {dinheiro(item['valor_unitario'])} = {dinheiro(item['subtotal'])}"
            )

    if valores_soltos:
        linhas.append("Valores adicionais:" if itens else "Valores somados:")
        for indice, valor in enumerate(valores_soltos, start=1):
            subtotal += valor
            linhas.append(f"- Valor {indice}: {dinheiro(valor)}")

    if subtotal <= 0:
        return None

    subtotal_credito = subtotal
    if desconto > 0:
        valor_desconto_extra = (subtotal * desconto / Decimal("100")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        subtotal_credito -= valor_desconto_extra
        linhas.append(f"Desconto aplicado ({desconto}%): -{dinheiro(valor_desconto_extra)}")

    pix = (subtotal_credito * Decimal("0.95")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    linhas.append("")
    linhas.append(f"Subtotal: {dinheiro(subtotal)}")
    linhas.append(f"Pix com 5% de desconto: {dinheiro(pix)}")

    if parcelas:
        if juros_mensal > 0:
            total_credito = (subtotal_credito * ((Decimal("1") + juros_mensal / Decimal("100")) ** parcelas)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            parcela = (total_credito / parcelas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            linhas.append(
                f"Credito em {parcelas}x com juros de {juros_mensal}% ao mes: {parcelas}x de {dinheiro(parcela)}"
            )
            linhas.append(f"Total no credito: {dinheiro(total_credito)}")
        else:
            parcela = (subtotal_credito / parcelas).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            linhas.append(f"Credito em {parcelas}x sem juros: {parcelas}x de {dinheiro(parcela)}")
    else:
        parcela_12x = (subtotal_credito / Decimal("12")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        linhas.append(f"Credito: ate 12x sem juros de {dinheiro(parcela_12x)}")

    return "\n".join(linhas)


def extrair_itens_pedido(texto, permitir_inferir=False):
    itens = []
    itens_incompletos = []
    spans = []
    qtd_regex = r'\d+|' + "|".join(NUMEROS_EXTENSO.keys())
    padrao_produto = re.compile(
        rf'(?<!\w)(?:(?P<qtd>{qtd_regex})\s+)?'
        r'(?P<produto>camisas?)\b'
        rf'(?P<detalhes>[^,;.]*?)(?=(?:\s+e\s+(?:(?:{qtd_regex})\s+)?camisas?\b)|$)'
    )

    for match in padrao_produto.finditer(texto):
        qtd = quantidade_para_int(match.group("qtd"))
        trecho_item = match.group(0)
        detalhes = match.group("detalhes") or ""
        cor = identificar_cor(trecho_item)
        tamanho = identificar_tamanho(detalhes)
        valor_match = re.search(r'(?:de|por|a)\s*(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)', detalhes)
        valor_unitario = numero_decimal(valor_match.group(1)) if valor_match else None
        item = montar_item_camisa(qtd, cor, tamanho, valor_unitario, match.span())
        spans.append(match.span())
        if item_tem_preco(item):
            itens.append(item)
        else:
            itens_incompletos.append(item)

    if itens or itens_incompletos or not permitir_inferir:
        return itens, itens_incompletos, spans

    padrao_inferido = re.compile(
        rf'(?<!\w)(?:(?P<qtd>{qtd_regex})\s+)?'
        r'(?P<detalhes>[a-z0-9\s]{1,45}?)\s+'
        r'(?:de|por|a)\s*(?:r\$\s*)?'
        r'(?P<valor>\d+(?:[.,]\d{1,2})?)'
    )
    for match in padrao_inferido.finditer(texto):
        trecho = match.group(0)
        if re.search(r'\b(?:desconto|juros|parcela|parcelas|credito|pix|boleto|total|soma|somar)\b', trecho):
            continue
        cor = identificar_cor(match.group("detalhes"))
        tamanho = identificar_tamanho(match.group("detalhes"))
        if not (cor or tamanho or re.search(r'\b(?:outra|outro|mais|nova|novo)\b', trecho)):
            continue
        qtd = quantidade_para_int(match.group("qtd"))
        valor_unitario = numero_decimal(match.group("valor"))
        itens.append(montar_item_camisa(qtd, cor, tamanho, valor_unitario, match.span()))
        spans.append(match.span())
        break

    return itens, itens_incompletos, spans


def adicionar_itens_carrinho(itens):
    global ultimo_item_index
    for item in itens:
        item.pop("span", None)
        carrinho.append(item)
        ultimo_item_index = len(carrinho) - 1


def limpar_carrinho():
    global ultimo_item_index
    carrinho.clear()
    ultimo_item_index = None


def indice_ultimo_item_valido():
    if ultimo_item_index is not None and 0 <= ultimo_item_index < len(carrinho):
        return ultimo_item_index
    return len(carrinho) - 1 if carrinho else None


def eh_comando_limpar_carrinho(texto):
    return bool(re.search(r'\b(?:limpar|esvaziar|zerar|cancelar|cancela)\b.*\b(?:carrinho|pedido|compra)\b', texto))


def eh_comando_resumo_carrinho(texto):
    if texto.strip() in ["pix", "boleto", "reembolso"]:
        return False
    return bool(re.search(
        r'\b(?:carrinho|pedido|total|tudo|quanto fica|quanto deu|somar|soma|fechar|pix|desconto|parcelar|parcelas|credito|dividir|divide)\b',
        texto
    ))


def eh_pergunta_total_carrinho(texto):
    return bool(re.search(
        r'\b(?:quanto fica|quanto deu|qual o total|total|tudo|resumo do pedido|pedido|carrinho)\b',
        texto
    ))


def eh_comando_remover_ultimo(texto):
    return bool(re.search(r'\b(?:remover|remove|tirar|tira|excluir|desfazer)\b.*\b(?:ultimo|ultima|item)\b', texto))


def eh_comando_trocar_ultimo(texto):
    tem_verbo_troca = re.search(r'\b(?:troca|trocar|substitui|substituir)\b', texto)
    tem_referencia_ultimo = re.search(r'\b(?:ultimo|ultima|ltima)\b', texto)
    return bool(tem_verbo_troca and (tem_referencia_ultimo or (" por " in texto and carrinho)))


def tentar_atualizar_ultimo_item(texto):
    indice = indice_ultimo_item_valido()
    if indice is None:
        return None

    item = carrinho[indice]
    qtd_match = re.search(r'\b(?:quantidade|qtd)\b.*?(?:para|por|em)?\s*(\d+)\b', texto)
    valor_match = re.search(r'\b(?:valor|preco|preco unitario|unitario)\b.*?(?:para|por|em)?\s*(?:r\$\s*)?(\d+(?:[.,]\d{1,2})?)', texto)

    if qtd_match:
        item["quantidade"] = int(qtd_match.group(1))
        atualizar_subtotal_item(item)
        return "Quantidade do ultimo item atualizada.\n" + montar_resumo_pedido()

    if valor_match:
        item["valor_unitario"] = numero_decimal(valor_match.group(1))
        atualizar_subtotal_item(item)
        return "Valor do ultimo item atualizado.\n" + montar_resumo_pedido()

    return None


def comando_csv_prioritario(texto):
    comandos = {
        "sair", "encerrar", "finalizar", "tchau", "ate logo",
        "cancelar atendimento", "falar com atendente", "quero falar com atendente",
        "atendente", "reembolso", "boleto", "pix"
    }
    return texto.strip() in comandos or texto.strip() in MENU_FINANCEIRO


def processar_calculo_financeiro(entrada_usuario, entrada_lower):
    """
    Intercepta pedidos de camisas, carrinho, soma, desconto e simulacao de credito.
    """
    global ultimo_item_index
    texto = entrada_lower

    palavras_chave_calculo = [
        "quanto fica", "qual valor total", "quanto vou pagar", "total somando",
        "somar", "soma", "calcular", "calcula", "orcamento", "orÃ§amento",
        "custa", "valor total", "preco", "preÃ§o", "desconto", "parcelar",
        "parcelas", "credito", "crÃ©dito", "juros", "pedido", "carrinho", "tudo"
    ]

    if comando_csv_prioritario(texto):
        return None

    if eh_comando_limpar_carrinho(texto):
        limpar_carrinho()
        return {
            "resposta": "Carrinho FashionFlow limpo. Podemos comecar um novo pedido de camisas quando quiser.",
            "tag": "calculo_concluido",
            "pergunta_seguinte": ""
        }

    if tem_produto_nao_suportado(texto):
        return {
            "resposta": resposta_produto_nao_suportado(),
            "tag": "calculo_concluido",
            "pergunta_seguinte": ""
        }

    if eh_comando_remover_ultimo(texto):
        indice = indice_ultimo_item_valido()
        if indice is None:
            resposta = "Ainda nao ha item no carrinho para remover."
        else:
            removido = carrinho.pop(indice)
            ultimo_item_index = len(carrinho) - 1 if carrinho else None
            resposta = f"Removi o ultimo item: {removido['quantidade']}x {nome_item_carrinho(removido)}.\n" + montar_resumo_pedido()
        return {
            "resposta": resposta,
            "tag": "calculo_concluido",
            "pergunta_seguinte": ""
        }

    if eh_comando_trocar_ultimo(texto):
        indice = indice_ultimo_item_valido()
        if indice is None:
            resposta = "Ainda nao ha item no carrinho para trocar."
        else:
            trecho_troca = texto.split(" por ", 1)[1] if " por " in texto else texto
            novos_itens, incompletos, _ = extrair_itens_pedido(trecho_troca, permitir_inferir=True)
            if incompletos or not novos_itens:
                resposta = "Posso trocar o ultimo item, mas preciso que voce informe a nova camisa com valor unitario ou tamanho."
            else:
                novo_item = novos_itens[0]
                novo_item.pop("span", None)
                carrinho[indice] = novo_item
                ultimo_item_index = indice
                resposta = "Ultimo item substituido.\n" + montar_resumo_pedido()
        return {
            "resposta": resposta,
            "tag": "calculo_concluido",
            "pergunta_seguinte": "Deseja seguir com Pix ou Cartao? (s/n)" if carrinho else ""
        }

    resposta_atualizacao = tentar_atualizar_ultimo_item(texto)
    if resposta_atualizacao:
        return {
            "resposta": resposta_atualizacao,
            "tag": "calculo_concluido",
            "pergunta_seguinte": "Deseja seguir com Pix ou Cartao? (s/n)"
        }

    permitir_inferir = bool(carrinho) or bool(re.search(r'\b(?:outra|outro|mais|nova|novo)\b', texto))
    itens, itens_incompletos, spans_itens = extrair_itens_pedido(texto, permitir_inferir=permitir_inferir)

    if itens_incompletos and not itens:
        return {
            "resposta": montar_resposta_item_incompleto(itens_incompletos),
            "tag": "calculo_concluido",
            "pergunta_seguinte": ""
        }

    if itens:
        adicionar_itens_carrinho(itens)
        resposta = "Item adicionado ao carrinho." if len(itens) == 1 else "Itens adicionados ao carrinho."
        return {
            "resposta": resposta + "\n" + montar_resumo_pedido(),
            "tag": "calculo_concluido",
            "pergunta_seguinte": "Deseja seguir com Pix ou Cartao? (s/n)"
        }

    if carrinho and eh_comando_resumo_carrinho(texto):
        parcelas = extrair_parcelas(texto)
        return {
            "resposta": montar_resumo_pedido(parcelas=parcelas),
            "tag": "calculo_concluido",
            "pergunta_seguinte": "Deseja seguir com Pix ou Cartao? (s/n)"
        }

    if not carrinho and eh_pergunta_total_carrinho(texto):
        return {
            "resposta": montar_resumo_pedido(),
            "tag": "calculo_concluido",
            "pergunta_seguinte": ""
        }

    if not any(c.isdigit() for c in texto):
        return None

    desconto = extrair_percentual(texto, ["desconto", "cupom", "promocao", "promoÃ§Ã£o"])
    juros_mensal = extrair_percentual(texto, ["juros", "taxa"])
    parcelas = extrair_parcelas(texto)
    valores_soltos = extrair_valores_soltos(texto, spans_itens)
    tem_intencao_calculo = any(k in texto for k in palavras_chave_calculo)
    tem_dois_ou_mais_valores = len(valores_soltos) >= 2

    if not (tem_intencao_calculo or tem_dois_ou_mais_valores):
        return None

    resposta = montar_resposta_calculo(
        [], valores_soltos, desconto, parcelas, juros_mensal
    )
    if not resposta:
        return None

    return {
        "resposta": resposta,
        "tag": "calculo_concluido",
        "pergunta_seguinte": "Deseja seguir com Pix ou Cartao? (s/n)"
    }


def buscar_resposta(mensagem):
    mensagem_norm = normalizar(mensagem)
    mensagem_norm = expandir_lexico_brasileiro(mensagem_norm)

    if mensagem_norm in ["cancelar atendimento", "cancelar o atendimento"]:
        return {
            "tag": "exit",
            "resposta": "Atendimento finalizado. Obrigado por falar com o Financeiro da FashionFlow.",
            "encerrar": True
        }

    for intencao in intencoes:
        for padrao in intencao["regex_palavras"]:
            if padrao.search(mensagem_norm):
                return intencao

    return {
        "tag": "fallback",
        "resposta": "Desculpe, não consegui compreender a sua dúvida financeira. Pode tentar explicar de outra forma?",
        "encerrar": False
    }


FALLBACK_RESPOSTA = "Desculpe, não consegui compreender a sua dúvida financeira. Pode tentar explicar de outra forma?"
RESPOSTAS_SIM = ["s", "sim", "ss", "aham", "claro",
                 "quero", "pode", "bora", "agora", "vamos", "confirmado"]
RESPOSTAS_NAO = ["n", "nao", "não", "negativo", "deixa",
                 "cancelar", "cancela", "nao quero", "desisto"]

MENU_FINANCEIRO = {
    "1": "cobranca incorreta", "cobranca": "cobranca incorreta", "cobrança": "cobranca incorreta",
    "2": "pagamento nao reconhecido", "fraude": "pagamento nao reconhecido", "contestacao": "pagamento nao reconhecido",
    "3": "paguei e nao constou", "conciliacao": "paguei e nao constou",
    "4": "reembolso", "estorno": "reembolso",
    "5": "nota fiscal", "nf": "nota fiscal",
    "6": "formas de pagamento", "formas": "formas de pagamento",
    "7": "extrato financeiro", "extrato": "extrato financeiro",
    "8": "status do pagamento", "status": "status do pagamento",
    "9": "negociar divida", "acordo": "negociar divida"
}

TAGS_QUE_PODEM_INTERROMPER_CONTEXTO = {
    "seguranca_bloqueio", "contestacao_fraude", "cobranca_duplicada_valor_incorreto",
    "conciliacao_pagamento", "reembolso", "nota_fiscal", "recusado_cartao_credito",
    "recusado_cartao_debito", "recusado_pix", "forma_pagamento", "pix", "boleto",
    "status_pagamento", "link_pagamento", "extrato_historico", "negociacao_divida",
    "atendimento_humano", "calculo_concluido"
}


def emitir_resultado(resultado):
    global contexto_pergunta
    bot_falar(resultado["resposta"])

    if resultado.get("pergunta_seguinte"):
        time.sleep(0.2)
        bot_falar(resultado["pergunta_seguinte"])
        contexto_pergunta = resultado["tag"]
    else:
        contexto_pergunta = None

    return not resultado.get("encerrar")


def parece_dado_credito(entrada_lower):
    tem_bandeira = any(b in entrada_lower for b in [
                       "visa", "master", "mastercard"])
    tem_parcela = re.search(
        r'(?<!\w)\d{1,2}\s*(x|vez|vezes|parcela|parcelas)(?!\w)', entrada_lower)
    return bool(tem_bandeira and tem_parcela)


def parece_dado_debito(entrada_lower):
    return any(b in entrada_lower for b in ["visa", "master", "mastercard"])


def entrada_muda_de_assunto(entrada, contexto_atual):
    resultado = buscar_resposta(entrada)
    tag = resultado.get("tag")
    if tag in TAGS_QUE_PODEM_INTERROMPER_CONTEXTO and tag != contexto_atual:
        return resultado
    return None

# ─────────────────────────────────────────────────────────────
#  PROCESSAMENTO DE CONTEXTOS FLUIDOS
# ─────────────────────────────────────────────────────────────


def processar_contexto(entrada, entrada_lower):
    global contexto_pergunta, tentativas_cep

    if entrada_lower in MENU_FINANCEIRO:
        emitir_resultado(buscar_resposta(MENU_FINANCEIRO[entrada_lower]))
        return True

    if contexto_pergunta == "aguardando_cep":
        if entrada_lower in ["sair", "cancelar", "n", "nao", "não"]:
            bot_falar("Sem problemas! Cancelamos o cálculo do frete operacional.")
            contexto_pergunta = None
            return True
        cep_limpo = entrada.replace("-", "").replace(" ", "")
        if cep_limpo.isdigit() and len(cep_limpo) == 8:
            bot_falar(f"CEP {entrada} validado com sucesso! 📍")
            bot_falar(
                "O prazo estimado para a entrega na sua região é de 3 a 7 dias úteis.")
            contexto_pergunta = None
        else:
            tentativas_cep += 1
            if tentativas_cep >= 3:
                bot_falar(
                    "Não consegui validar seu CEP. Vamos retornar ao menu principal.")
                contexto_pergunta = None
                tentativas_cep = 0
            else:
                bot_falar(
                    f"Formato inválido. Digite apenas 8 dígitos numéricos (Tentativa {tentativas_cep}/3):")
        return True

    if contexto_pergunta == "credito":
        novo_assunto = entrada_muda_de_assunto(entrada, contexto_pergunta)
        if novo_assunto:
            emitir_resultado(novo_assunto)
            return True
        if not parece_dado_credito(entrada_lower):
            bot_falar(
                "Para seguir no crédito, informe a bandeira e as parcelas (Ex: Visa, 3x). Se quiser mudar de assunto, diga Pix, boleto ou cobrança.")
            return True
        bot_falar(
            "Perfeito! Redirecionando para o ambiente de checkout seguro para digitação dos dados confidenciais... 💳")
        contexto_pergunta = None
        return True

    if contexto_pergunta in ["parcela", "debito"]:
        novo_assunto = entrada_muda_de_assunto(entrada, contexto_pergunta)
        if novo_assunto:
            emitir_resultado(novo_assunto)
            return True
        dado_valido = parece_dado_credito(
            entrada_lower) if contexto_pergunta == "parcela" else parece_dado_debito(entrada_lower)
        if not dado_valido:
            bot_falar("Preciso de uma informação válida para prosseguir. Para débito diga Visa/Master. Para parcelas diga Bandeira e Vezes (Ex: Visa, 3x).")
            return True
        bot_falar(f"Registrado com sucesso. Redirecionando para o gateway seguro.")
        contexto_pergunta = None
        return True

    if contexto_pergunta and entrada_lower in RESPOSTAS_SIM + RESPOSTAS_NAO:
        respondeu_sim = entrada_lower in RESPOSTAS_SIM
        if respondeu_sim:
            if contexto_pergunta in ["pix", "desconto", "calculo_concluido"]:
                bot_falar(
                    "Aqui estão os dados oficiais para transferência segura via Pix: 👇")
                bot_falar(
                    "Chave CNPJ: 12.345.678/0001-99 (FashionFlow Pagamentos Ltda)")
                bot_falar(
                    "A compensação ocorre instantaneamente. Posso ajudar em algo mais?")
                contexto_pergunta = None
            elif contexto_pergunta == "contestacao_fraude":
                bot_falar(
                    "Entendido. Gerando token de segurança e transferindo para o Setor Antifraude... 🧑‍💻")
                contexto_pergunta = None
            elif contexto_pergunta == "reembolso":
                bot_falar(
                    "Certo! Acesse o portal oficial para auditoria: financeiro.fashionflow.com/reembolsos")
                contexto_pergunta = None
            elif contexto_pergunta == "atendimento_humano":
                bot_falar(
                    "Conectando com o suporte humano agora mesmo... 👤 Por favor, aguarde.")
                contexto_pergunta = None
            else:
                bot_falar("Perfeito! Como posso te ajudar agora?")
                contexto_pergunta = None
        else:
            bot_falar("Entendido. Operação cancelada. Como posso ser útil agora?")
            contexto_pergunta = None
        return True

    return False


def processar_intencao(entrada):
    global contexto_pergunta, sem_entender
    resultado = buscar_resposta(entrada)
    continuar = emitir_resultado(resultado)

    if resultado.get("tag") != "fallback":
        sem_entender = 0
    else:
        sem_entender += 1
        if sem_entender >= 3:
            bot_falar("Percebi que suas dúvidas demandam atenção personalizada.")
            bot_falar(
                "Gostaria que eu realizasse o transbordo para um atendente humano analisar seu caso? (s/n)")
            contexto_pergunta = "atendimento_humano"
            sem_entender = 0
    return continuar

# ─────────────────────────────────────────────────────────────
#  INICIALIZAÇÃO DO SISTEMA
# ─────────────────────────────────────────────────────────────


try:
    intencoes = carregar_intencoes("base_conhecimento.csv")
except FileNotFoundError:
    print(f"{RED}❌ ERRO CRÍTICO: Arquivo 'base_conhecimento.csv' não localizado.{RESET}")
    sys.exit(1)

contexto_pergunta = None
tentativas_cep = 0
sem_entender = 0
historico_conversa = []
memoria_repeticao = []
historico_recente = []
carrinho = []
ultimo_item_index = None

registrar_log(
    "Sistema", f"=== Nova sessão iniciada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ===")

print(f"{CYAN}─────────────────────────────────────────────────────────────{RESET}")
print(f"{CYAN}       {BOLD}🌟 CHATBOT FINANCEIRO FASHIONFLOW V2.0 🌟{RESET}")
print(f"{CYAN}─────────────────────────────────────────────────────────────{RESET}")
print(f"Loading: {YELLOW}Mapeando {len(intencoes)} intenções financeiras do CSV... {GREEN}Pronto!{RESET}\n")
print(f"{GREEN}Bot: Olá! Como posso te ajudar com o financeiro hoje?{RESET}")

# ─────────────────────────────────────────────────────────────
#  LOOP PRINCIPAL COM QUEBRA DE CONTEXTO POR INTENÇÃO MATEMÁTICA
# ─────────────────────────────────────────────────────────────
while True:
    try:
        entrada = input(f"{BOLD}Você: {RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        print()
        bot_falar("Atendimento finalizado preventivamente. Até logo! 👋")
        break

    if not entrada:
        continue

    entrada_lower = normalizar(entrada)
    registrar_log("Você", entrada)
    historico_conversa.append({"quem": "usuario", "msg": entrada})

    # Interceptador dinâmico de comandos de repetição
    if entrada_lower in ["repete", "manda de novo", "fala de novo", "repete ai", "manda de novo ai"]:
        mensagens_para_repetir = historico_recente or memoria_repeticao
        if mensagens_para_repetir:
            for msg in mensagens_para_repetir:
                time.sleep(0.2)
                print(f"{GREEN}Bot (Repetindo): {msg}{RESET}")
        else:
            print(f"{YELLOW}Bot: Não há mensagens recentes para repetir.{RESET}")
        continue

    memoria_repeticao = list(historico_recente)
    historico_recente.clear()

    # 🚀 INTERCEPTADOR MATEMÁTICO DE ALTA PRIORIDADE (Garante acerto nos Benchmarks)
    resultado_calculo = processar_calculo_financeiro(entrada, entrada_lower)
    if resultado_calculo:
        emitir_resultado(resultado_calculo)
        continue

    # 1. Fluxo de contexto regular
    if processar_contexto(entrada, entrada_lower):
        continue

    # 2. Busca regular de intenções por palavra-chave mapeadas no CSV
    continuar = processar_intencao(entrada)
    if not continuar:
        break

registrar_log("Sistema", "=== Sessão encerrada de forma limpa ===\n")
