import sys
import time
from datetime import datetime

from .config import BOT_TITLE, ChatbotState, KNOWLEDGE_BASE_FILE, MENU_FINANCEIRO, REPEAT_COMMANDS
from .context_engine import processar_contexto
from .finance_calculator import processar_calculo_financeiro
from .intent_engine import buscar_resposta
from .knowledge_base import carregar_intencoes
from .logger import registrar_log
from .utils import normalizar


RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RED = "\033[91m"


def configurar_saida_terminal():
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8")


class TerminalChatbot:
    def __init__(self):
        self.state = ChatbotState()
        self.intencoes = carregar_intencoes(KNOWLEDGE_BASE_FILE)

    def bot_falar(self, texto, efeito_digitacao=True):
        time.sleep(0.4)
        registrar_log("Bot", texto)
        self.state.historico_conversa.append({"quem": "bot", "msg": texto})
        self.state.historico_recente.append(texto)

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

    def emitir_resultado(self, resultado):
        self.bot_falar(resultado["resposta"])
        if resultado.get("pergunta_seguinte"):
            time.sleep(0.2)
            self.bot_falar(resultado["pergunta_seguinte"])
            self.state.contexto_pergunta = resultado["tag"]
        else:
            self.state.contexto_pergunta = None
        return not resultado.get("encerrar")

    def processar_intencao(self, entrada):
        resultado = buscar_resposta(entrada, self.intencoes)
        continuar = self.emitir_resultado(resultado)
        if resultado.get("tag") != "fallback":
            self.state.sem_entender = 0
        else:
            self.state.sem_entender += 1
            if self.state.sem_entender >= 3:
                self.bot_falar("Percebi que suas dúvidas demandam atenção personalizada.")
                self.bot_falar("Gostaria que eu realizasse o transbordo para um atendente humano analisar seu caso? (s/n)")
                self.state.contexto_pergunta = "atendimento_humano"
                self.state.sem_entender = 0
        return continuar

    def exibir_cabecalho(self):
        print(f"{CYAN}─────────────────────────────────────────────────────────────{RESET}")
        print(f"{CYAN}       {BOLD}🌟 {BOT_TITLE} 🌟{RESET}")
        print(f"{CYAN}─────────────────────────────────────────────────────────────{RESET}")
        print(f"Loading: {YELLOW}Mapeando {len(self.intencoes)} intenções financeiras do CSV... {GREEN}Pronto!{RESET}\n")
        print(f"{GREEN}Bot: Olá! Como posso te ajudar com o financeiro hoje?{RESET}")

    def processar_repeticao(self, entrada_lower):
        if entrada_lower not in REPEAT_COMMANDS:
            return False
        mensagens_para_repetir = self.state.historico_recente or self.state.memoria_repeticao
        if mensagens_para_repetir:
            for mensagem in mensagens_para_repetir:
                time.sleep(0.2)
                print(f"{GREEN}Bot (Repetindo): {mensagem}{RESET}")
        else:
            print(f"{YELLOW}Bot: Não há mensagens recentes para repetir.{RESET}")
        return True

    def run(self):
        registrar_log("Sistema", f"=== Nova sessão iniciada em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} ===")
        self.exibir_cabecalho()

        while True:
            try:
                entrada = input(f"{BOLD}Você: {RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print()
                self.bot_falar("Atendimento finalizado preventivamente. Até logo! 👋")
                break

            if not entrada:
                continue

            entrada_lower = normalizar(entrada)
            registrar_log("Você", entrada)
            self.state.historico_conversa.append({"quem": "usuario", "msg": entrada})

            if self.processar_repeticao(entrada_lower):
                continue

            self.state.memoria_repeticao = list(self.state.historico_recente)
            self.state.historico_recente.clear()

            resultado_calculo = processar_calculo_financeiro(self.state, entrada, entrada_lower, MENU_FINANCEIRO)
            if resultado_calculo:
                self.emitir_resultado(resultado_calculo)
                continue

            if processar_contexto(self.state, entrada, entrada_lower, self.intencoes, self.emitir_resultado, self.bot_falar):
                continue

            if not self.processar_intencao(entrada):
                break

        registrar_log("Sistema", "=== Sessão encerrada de forma limpa ===\n")


def run_chatbot():
    configurar_saida_terminal()
    try:
        TerminalChatbot().run()
    except FileNotFoundError:
        print(f"{RED}ERRO CRITICO: Arquivo '{KNOWLEDGE_BASE_FILE}' nao localizado.{RESET}")
        raise
