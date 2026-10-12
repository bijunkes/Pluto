# Cápsula de reprodução

## Base

- Data: 2026-09-24
- Sistema: Windows
- Runtime: Python da `.venv`
- Escopo: `TelegramBot.menu_callback`

## Comando

Execução isolada do handler com `query.answer()` configurado para lançar `telegram.error.BadRequest` com a mensagem `Query is too old and response timeout expired or query id is invalid`.

## Resultado

- Exit code: 0
- Saída relevante: `edit_calls=0`
- Taxa: 1 falha em 1 tentativa
- Classificação: deterministic

## Conclusão

A exceção é capturada em `menu_callback`, mas o retorno imediato encerra a interação sem editar a mensagem nem enviar orientação. A evidência confirma o caminho causal do relato.

## Prova vermelha automatizada

Comando: `.venv/Scripts/python.exe -m pytest -q tests/test_callback_handling.py`

- Exit code: 1
- Resultado: 2 falhas e 1 teste aprovado
- Falha 1: a orientação esperada foi enviada zero vezes
- Falha 2: `RuntimeError` inesperado foi silenciosamente capturado
