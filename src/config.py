from dataclasses import dataclass, field
from decimal import Decimal

from .cart import Cart


COMPANY_NAME = "FashionFlow"
BOT_TITLE = "CHATBOT FINANCEIRO FASHIONFLOW V2.0"
KNOWLEDGE_BASE_FILE = "base_conhecimento.csv"
LOG_FILE = "log_atendimento.txt"

PIX_DISCOUNT_RATE = Decimal("0.05")
MAX_CREDIT_INSTALLMENTS = 12

DEFAULT_FALLBACK_RESPONSE = (
    "Desculpe, não consegui compreender a sua dúvida financeira. "
    "Pode tentar explicar de outra forma?"
)

EMPTY_CART_MESSAGE = (
    "Seu carrinho está vazio no momento. Me diga quais camisas deseja adicionar "
    "para eu calcular o total."
)

UNSUPPORTED_PRODUCT_MESSAGE = (
    "No momento a FashionFlow trabalha apenas com camisas. "
    "Posso calcular seu pedido de camisas se voce informar quantidade, cor e valor unitario ou tamanho."
)

MENU_FINANCEIRO = {
    "1": "cobranca incorreta",
    "cobranca": "cobranca incorreta",
    "cobrança": "cobranca incorreta",
    "2": "pagamento nao reconhecido",
    "fraude": "pagamento nao reconhecido",
    "contestacao": "pagamento nao reconhecido",
    "3": "paguei e nao constou",
    "conciliacao": "paguei e nao constou",
    "4": "reembolso",
    "estorno": "reembolso",
    "5": "nota fiscal",
    "nf": "nota fiscal",
    "6": "formas de pagamento",
    "formas": "formas de pagamento",
    "7": "extrato financeiro",
    "extrato": "extrato financeiro",
    "8": "status do pagamento",
    "status": "status do pagamento",
    "9": "negociar divida",
    "acordo": "negociar divida",
}

RESPOSTAS_SIM = [
    "s", "sim", "ss", "aham", "claro", "quero", "pode",
    "bora", "agora", "vamos", "confirmado",
]

RESPOSTAS_NAO = [
    "n", "nao", "não", "negativo", "deixa", "cancelar",
    "cancela", "nao quero", "desisto",
]

TAGS_QUE_PODEM_INTERROMPER_CONTEXTO = {
    "seguranca_bloqueio",
    "contestacao_fraude",
    "cobranca_duplicada_valor_incorreto",
    "conciliacao_pagamento",
    "reembolso",
    "nota_fiscal",
    "recusado_cartao_credito",
    "recusado_cartao_debito",
    "recusado_pix",
    "forma_pagamento",
    "pix",
    "boleto",
    "status_pagamento",
    "link_pagamento",
    "extrato_historico",
    "negociacao_divida",
    "atendimento_humano",
    "calculo_concluido",
}

REPEAT_COMMANDS = {
    "repete",
    "manda de novo",
    "fala de novo",
    "repete ai",
    "manda de novo ai",
}


@dataclass
class ChatbotState:
    contexto_pergunta: str | None = None
    tentativas_cep: int = 0
    sem_entender: int = 0
    historico_conversa: list[dict[str, str]] = field(default_factory=list)
    memoria_repeticao: list[str] = field(default_factory=list)
    historico_recente: list[str] = field(default_factory=list)
    cart: Cart = field(default_factory=Cart)
