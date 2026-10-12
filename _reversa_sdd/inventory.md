# Inventário inicial do Projeto-Final-Entra21

Data: 2026-09-17. Escopo: reconhecimento superficial pelo Scout, sem análise completa de regras de negócio.

## Estrutura

- `main.py`: inicializa o bot Telegram.
- `src/telegram/`: handlers do bot e roteador de skills.
- `src/services/`: conversa, IA, compras, resumos, planejamento de economia, autenticação e agendamento.
- `src/api/`: API FastAPI e schemas.
- `src/database/`: acesso PostgreSQL via psycopg.
- `src/config/`: categorias.
- `dashboard/`: interface HTML, CSS e JavaScript.
- `tests/`: testes Python.

## Entradas e configuração

- Bot: `main.py` e `src/telegram/telegram_bot.py` (`run_polling`).
- API: `src/api/main.py` (`app` FastAPI).
- Testes: `pytest.ini`; dependências em `requirements.txt` e `requirements-dev.txt`.
- Variáveis locais: `.env` (conteúdo e segredos não reproduzidos aqui).
- Não foram identificados Dockerfile, workflow CI nem migrações SQL na superfície examinada.

## Observações verificadas

- 🟢 CONFIRMADO: `src/telegram/telegram_bot.py` tem 1.772 linhas e concentra estados, callbacks e roteamento de mensagens.
- 🟢 CONFIRMADO: `pytest.ini` restringe a descoberta a três arquivos `test_*.py`, embora existam outros testes no diretório.
- 🟢 CONFIRMADO: estados de conversa e planejamento usam `context.user_data`; não há configuração de persistência do `python-telegram-bot` no arquivo do bot.
- 🟡 INFERIDO: após reinício do processo, o usuário pode perder o estágio de um fluxo em andamento. Validar em execução integrada.
