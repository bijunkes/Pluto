# Cápsula de reprodução

## Ambiente

- Data: 2026-09-24
- Sistema: Windows
- Runtime: Python da `.venv`
- Script: `evidence/reproduce_event_loop.py`

## Procedimento

`CompraService.listar_compras()` foi substituído por uma operação síncrona de 200 ms. Em paralelo, um heartbeat assíncrono deveria acordar após 10 ms.

## Resultado

- Comando: `.venv/Scripts/python.exe evidence/reproduce_event_loop.py`
- Exit code: 1
- Heartbeat observado: 215 ms
- Taxa: 1 falha em 1 tentativa
- Classificação: deterministic

## Conclusão

A chamada síncrona dentro de `TelegramBot.listar_compras` bloqueia o event loop e atrasa tarefas independentes. O mesmo padrão aparece em listagens, cadastros e confirmações que acessam `CompraService` diretamente.

## Prova vermelha automatizada

- Comando: `.venv/Scripts/python.exe -m pytest -q tests/test_bot_responsiveness.py`
- Exit code: 1
- Resultado: 2 falhas
- Evidência 1: `AssertionError: event loop ficou bloqueado`
- Evidência 2: `asyncio.to_thread` aguardado zero vezes na consulta de contas
