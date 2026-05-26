# Chatbot Financeiro FashionFlow - Versão mesclada

Esta versão mantém a lógica estável apresentada pelo grupo e incorpora apenas as contribuições seguras da versão modificada:

- novas palavras-chave úteis em formas de pagamento, descontos, extrato, Pix, conciliação e dados bancários;
- novas intenções para empréstimo e falha de retorno de estorno;
- correção de prioridade para pagamento misto continuar antes de Pix/cartão;
- remoção de conflitos que faziam cobrança indevida cair como fraude;
- remoção de mudanças de código que reintroduziam CEP/frete, cálculo de produtos e estilização ANSI.

Arquivos principais:
- `chatbot.py`
- `gerar_csv.py`
- `base_conhecimento.csv`
- `log_atendimento.txt`
