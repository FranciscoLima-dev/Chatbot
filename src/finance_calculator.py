import re
from decimal import Decimal, ROUND_HALF_UP

from .config import (
    EMPTY_CART_MESSAGE,
    MAX_CREDIT_INSTALLMENTS,
    PIX_DISCOUNT_RATE,
    UNSUPPORTED_PRODUCT_MESSAGE,
)
from .product_parser import (
    eh_comando_limpar_carrinho,
    eh_comando_remover_ultimo,
    eh_comando_resumo_carrinho,
    eh_comando_trocar_ultimo,
    eh_pergunta_total_carrinho,
    extrair_atualizacao_ultimo_item,
    extrair_itens_pedido,
    extrair_parcelas,
    extrair_percentual,
    extrair_valores_soltos,
    tem_produto_nao_suportado,
)
from .utils import dinheiro


CALCULATION_KEYWORDS = [
    "quanto fica",
    "qual valor total",
    "quanto vou pagar",
    "total somando",
    "somar",
    "soma",
    "calcular",
    "calcula",
    "orcamento",
    "orçamento",
    "custa",
    "valor total",
    "preco",
    "preço",
    "desconto",
    "parcelar",
    "parcelas",
    "credito",
    "crédito",
    "juros",
    "pedido",
    "carrinho",
    "tudo",
]

CSV_PRIORITY_COMMANDS = {
    "sair",
    "encerrar",
    "finalizar",
    "tchau",
    "ate logo",
    "cancelar atendimento",
    "falar com atendente",
    "quero falar com atendente",
    "atendente",
    "reembolso",
    "boleto",
    "pix",
}


def nome_item(item):
    partes = ["Camisa"]
    if item.cor:
        partes.append(item.cor)
    if item.tamanho:
        partes.append(f"tamanho {item.tamanho.upper()}")
    return " ".join(partes)


def montar_resumo_pedido(cart, parcelas=None):
    itens = cart.listar_itens()
    itens_com_preco = [item for item in itens if item.valor_unitario is not None]
    if not itens_com_preco:
        return EMPTY_CART_MESSAGE

    linhas = ["\nResumo do pedido FashionFlow:"]
    subtotal = Decimal("0")
    for item in itens_com_preco:
        subtotal += item.subtotal
        linhas.append(f"- {item.quantidade}x {nome_item(item)} de {dinheiro(item.valor_unitario)} = {dinheiro(item.subtotal)}")

    pix = calcular_pix(subtotal)
    parcela_12x = (subtotal / Decimal(MAX_CREDIT_INSTALLMENTS)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    linhas.append("")
    linhas.append(f"Subtotal: {dinheiro(subtotal)}")
    if parcelas:
        parcela = calcular_parcela_credito(subtotal, parcelas)
        linhas.append(f"Crédito em {parcelas}x sem juros: {parcelas}x de {dinheiro(parcela)}")
        linhas.append(f"Pix com 5% de desconto: {dinheiro(pix)}")
    else:
        linhas.append(f"Pix com 5% de desconto: {dinheiro(pix)}")
        linhas.append(f"Crédito: ate 12x sem juros de {dinheiro(parcela_12x)}")
    return "\n".join(linhas)


def montar_resposta_item_incompleto(itens_incompletos):
    total_qtd = sum(item.quantidade for item in itens_incompletos)
    produto = "camisa" if total_qtd == 1 else "camisas"
    return (
        f"Encontrei {total_qtd} {produto}, mas preciso do valor unitario ou do tamanho antes de calcular. "
        "Voce pode dizer, por exemplo: 'sao 16 camisas de 150' ou '16 camisas tamanho M'."
    )


def calcular_pix(subtotal):
    return (subtotal * (Decimal("1") - PIX_DISCOUNT_RATE)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_parcela_credito(subtotal, parcelas):
    return (subtotal / Decimal(parcelas)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def montar_resposta_calculo_solto(valores_soltos, desconto, parcelas, juros_mensal):
    linhas = ["\nResumo do pedido FashionFlow:"]
    subtotal = Decimal("0")
    if valores_soltos:
        linhas.append("Valores somados:")
    for indice, valor in enumerate(valores_soltos, start=1):
        subtotal += valor
        linhas.append(f"- Valor {indice}: {dinheiro(valor)}")
    if subtotal <= 0:
        return None

    subtotal_credito = subtotal
    if desconto > 0:
        valor_desconto = (subtotal * desconto / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal_credito -= valor_desconto
        linhas.append(f"Desconto aplicado ({desconto}%): -{dinheiro(valor_desconto)}")

    linhas.append("")
    linhas.append(f"Subtotal: {dinheiro(subtotal)}")
    linhas.append(f"Pix com 5% de desconto: {dinheiro(calcular_pix(subtotal_credito))}")
    if parcelas:
        if juros_mensal > 0:
            total_credito = (subtotal_credito * ((Decimal("1") + juros_mensal / Decimal("100")) ** parcelas)).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
            parcela = calcular_parcela_credito(total_credito, parcelas)
            linhas.append(f"Credito em {parcelas}x com juros de {juros_mensal}% ao mes: {parcelas}x de {dinheiro(parcela)}")
            linhas.append(f"Total no credito: {dinheiro(total_credito)}")
        else:
            parcela = calcular_parcela_credito(subtotal_credito, parcelas)
            linhas.append(f"Credito em {parcelas}x sem juros: {parcelas}x de {dinheiro(parcela)}")
    else:
        parcela_12x = calcular_parcela_credito(subtotal_credito, MAX_CREDIT_INSTALLMENTS)
        linhas.append(f"Credito: ate 12x sem juros de {dinheiro(parcela_12x)}")
    return "\n".join(linhas)


def resultado(resposta, pergunta_seguinte=""):
    return {
        "resposta": resposta,
        "tag": "calculo_concluido",
        "pergunta_seguinte": pergunta_seguinte,
    }


def processar_calculo_financeiro(state, entrada_usuario, entrada_lower, menu_financeiro):
    texto = entrada_lower
    cart = state.cart

    if texto.strip() in CSV_PRIORITY_COMMANDS or texto.strip() in menu_financeiro:
        return None

    if eh_comando_limpar_carrinho(texto):
        cart.limpar()
        return resultado("Carrinho FashionFlow limpo. Podemos comecar um novo pedido de camisas quando quiser.")

    if tem_produto_nao_suportado(texto):
        return resultado(UNSUPPORTED_PRODUCT_MESSAGE)

    if eh_comando_remover_ultimo(texto):
        removido = cart.remover_ultimo_item()
        if removido is None:
            resposta = "Ainda nao ha item no carrinho para remover."
        else:
            resposta = f"Removi o ultimo item: {removido.quantidade}x {nome_item(removido)}.\n" + montar_resumo_pedido(cart)
        return resultado(resposta)

    if eh_comando_trocar_ultimo(texto, not cart.esta_vazio()):
        if cart.esta_vazio():
            resposta = "Ainda nao ha item no carrinho para trocar."
        else:
            trecho_troca = texto.split(" por ", 1)[1] if " por " in texto else texto
            novos_itens, incompletos, _ = extrair_itens_pedido(trecho_troca, permitir_inferir=True)
            if incompletos or not novos_itens:
                resposta = "Posso trocar o ultimo item, mas preciso que voce informe a nova camisa com valor unitario ou tamanho."
            else:
                cart.trocar_ultimo_item(novos_itens[0])
                resposta = "Ultimo item substituido.\n" + montar_resumo_pedido(cart)
        pergunta = "Deseja seguir com Pix ou Cartao? (s/n)" if not cart.esta_vazio() else ""
        return resultado(resposta, pergunta)

    campo, valor = extrair_atualizacao_ultimo_item(texto)
    if campo == "quantidade" and cart.atualizar_quantidade_ultimo(valor):
        return resultado("Quantidade do ultimo item atualizada.\n" + montar_resumo_pedido(cart), "Deseja seguir com Pix ou Cartao? (s/n)")
    if campo == "valor" and cart.atualizar_valor_ultimo(valor):
        return resultado("Valor do ultimo item atualizado.\n" + montar_resumo_pedido(cart), "Deseja seguir com Pix ou Cartao? (s/n)")

    permitir_inferir = not cart.esta_vazio() or bool(re.search(r"\b(?:outra|outro|mais|nova|novo)\b", texto))
    itens, itens_incompletos, spans_itens = extrair_itens_pedido(texto, permitir_inferir=permitir_inferir)

    if itens_incompletos and not itens:
        return resultado(montar_resposta_item_incompleto(itens_incompletos))

    if itens:
        cart.adicionar_itens(itens)
        prefixo = "Item adicionado ao carrinho." if len(itens) == 1 else "Itens adicionados ao carrinho."
        return resultado(prefixo + "\n" + montar_resumo_pedido(cart), "Deseja seguir com Pix ou Cartao? (s/n)")

    if not cart.esta_vazio() and eh_comando_resumo_carrinho(texto):
        parcelas = extrair_parcelas(texto, MAX_CREDIT_INSTALLMENTS)
        return resultado(montar_resumo_pedido(cart, parcelas=parcelas), "Deseja seguir com Pix ou Cartao? (s/n)")

    if cart.esta_vazio() and eh_pergunta_total_carrinho(texto):
        return resultado(montar_resumo_pedido(cart))

    if not any(caractere.isdigit() for caractere in texto):
        return None

    desconto = extrair_percentual(texto, ["desconto", "cupom", "promocao", "promoção"])
    juros_mensal = extrair_percentual(texto, ["juros", "taxa"])
    parcelas = extrair_parcelas(texto, MAX_CREDIT_INSTALLMENTS)
    valores_soltos = extrair_valores_soltos(texto, spans_itens)
    tem_intencao_calculo = any(palavra in texto for palavra in CALCULATION_KEYWORDS)
    tem_dois_ou_mais_valores = len(valores_soltos) >= 2

    if not (tem_intencao_calculo or tem_dois_ou_mais_valores):
        return None

    resposta = montar_resposta_calculo_solto(valores_soltos, desconto, parcelas, juros_mensal)
    if not resposta:
        return None
    return resultado(resposta, "Deseja seguir com Pix ou Cartao? (s/n)")
