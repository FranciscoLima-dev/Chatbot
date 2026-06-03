import re

from .config import MENU_FINANCEIRO, RESPOSTAS_NAO, RESPOSTAS_SIM, TAGS_QUE_PODEM_INTERROMPER_CONTEXTO
from .intent_engine import buscar_resposta


def parece_dado_credito(entrada_lower):
    tem_bandeira = any(bandeira in entrada_lower for bandeira in ["visa", "master", "mastercard"])
    tem_parcela = re.search(r"(?<!\w)\d{1,2}\s*(x|vez|vezes|parcela|parcelas)(?!\w)", entrada_lower)
    return bool(tem_bandeira and tem_parcela)


def parece_dado_debito(entrada_lower):
    return any(bandeira in entrada_lower for bandeira in ["visa", "master", "mastercard"])


def entrada_muda_de_assunto(entrada, contexto_atual, intencoes):
    resultado = buscar_resposta(entrada, intencoes)
    tag = resultado.get("tag")
    if tag in TAGS_QUE_PODEM_INTERROMPER_CONTEXTO and tag != contexto_atual:
        return resultado
    return None


def processar_contexto(state, entrada, entrada_lower, intencoes, emitir_resultado, bot_falar):
    if entrada_lower in MENU_FINANCEIRO:
        emitir_resultado(buscar_resposta(MENU_FINANCEIRO[entrada_lower], intencoes))
        return True

    if state.contexto_pergunta == "aguardando_cep":
        if entrada_lower in ["sair", "cancelar", "n", "nao", "não"]:
            bot_falar("Sem problemas! Cancelamos o cálculo do frete operacional.")
            state.contexto_pergunta = None
            return True
        cep_limpo = entrada.replace("-", "").replace(" ", "")
        if cep_limpo.isdigit() and len(cep_limpo) == 8:
            bot_falar(f"CEP {entrada} validado com sucesso! 📍")
            bot_falar("O prazo estimado para a entrega na sua região é de 3 a 7 dias úteis.")
            state.contexto_pergunta = None
        else:
            state.tentativas_cep += 1
            if state.tentativas_cep >= 3:
                bot_falar("Não consegui validar seu CEP. Vamos retornar ao menu principal.")
                state.contexto_pergunta = None
                state.tentativas_cep = 0
            else:
                bot_falar(f"Formato inválido. Digite apenas 8 dígitos numéricos (Tentativa {state.tentativas_cep}/3):")
        return True

    if state.contexto_pergunta == "credito":
        novo_assunto = entrada_muda_de_assunto(entrada, state.contexto_pergunta, intencoes)
        if novo_assunto:
            emitir_resultado(novo_assunto)
            return True
        if not parece_dado_credito(entrada_lower):
            bot_falar("Para seguir no crédito, informe a bandeira e as parcelas (Ex: Visa, 3x). Se quiser mudar de assunto, diga Pix, boleto ou cobrança.")
            return True
        bot_falar("Perfeito! Redirecionando para o ambiente de checkout seguro para digitação dos dados confidenciais... 💳")
        state.contexto_pergunta = None
        return True

    if state.contexto_pergunta in ["parcela", "debito"]:
        novo_assunto = entrada_muda_de_assunto(entrada, state.contexto_pergunta, intencoes)
        if novo_assunto:
            emitir_resultado(novo_assunto)
            return True
        dado_valido = parece_dado_credito(entrada_lower) if state.contexto_pergunta == "parcela" else parece_dado_debito(entrada_lower)
        if not dado_valido:
            bot_falar("Preciso de uma informação válida para prosseguir. Para débito diga Visa/Master. Para parcelas diga Bandeira e Vezes (Ex: Visa, 3x).")
            return True
        bot_falar("Registrado com sucesso. Redirecionando para o gateway seguro.")
        state.contexto_pergunta = None
        return True

    if state.contexto_pergunta and entrada_lower in RESPOSTAS_SIM + RESPOSTAS_NAO:
        respondeu_sim = entrada_lower in RESPOSTAS_SIM
        if respondeu_sim:
            if state.contexto_pergunta in ["pix", "desconto", "calculo_concluido"]:
                bot_falar("Aqui estão os dados oficiais para transferência segura via Pix: 👇")
                bot_falar("Chave CNPJ: 12.345.678/0001-99 (FashionFlow Pagamentos Ltda)")
                bot_falar("A compensação ocorre instantaneamente. Posso ajudar em algo mais?")
            elif state.contexto_pergunta == "contestacao_fraude":
                bot_falar("Entendido. Gerando token de segurança e transferindo para o Setor Antifraude... 🧑‍💻")
            elif state.contexto_pergunta == "reembolso":
                bot_falar("Certo! Acesse o portal oficial para auditoria: financeiro.fashionflow.com/reembolsos")
            elif state.contexto_pergunta == "atendimento_humano":
                bot_falar("Conectando com o suporte humano agora mesmo... 👤 Por favor, aguarde.")
            else:
                bot_falar("Perfeito! Como posso te ajudar agora?")
        else:
            bot_falar("Entendido. Operação cancelada. Como posso ser útil agora?")
        state.contexto_pergunta = None
        return True

    return False
