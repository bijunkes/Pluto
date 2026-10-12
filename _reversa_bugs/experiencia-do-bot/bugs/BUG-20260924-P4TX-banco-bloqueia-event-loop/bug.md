---
schema_version: 1
id: BUG-20260924-P4TX
display_number: 2
title: Operações de banco bloqueiam o event loop do Telegram
status: resolved
phase: delivering
severity: high
priority: P1
created: 2026-09-24
updated: 2026-09-24
origin:
  type: inspection
  external_ref: null
area: unclassified
module: unclassified
feature: unclassified
labels: []
visibility: normal
security_suspected: false
reproduction:
  classification: deterministic
  rate: "10/10 sob latência de banco"
  suspected_triggers: ["consulta síncrona ao PostgreSQL dentro de handler assíncrono"]
blocking: []
relationships:
  - bug: BUG-20260924-R6NV
    type: related-to
    state: proposed
    evidence: []
traceability:
  specs: ["_reversa_forward/001-intencoes-financeiras/requirements.md#6-requisitos-não-funcionais"]
  affected_code: ["src/telegram/telegram_bot.py", "src/services/compra_service.py", "src/database/database.py"]
  root_cause:
    state: confirmed
    hypothesis: "handlers assíncronos executam métodos síncronos de banco diretamente no event loop"
    causal_path:
      - "handler assíncrono recebe interação"
      - "CompraService chama Database de forma síncrona"
      - "espera de I/O ocupa a thread do event loop"
      - "outras interações aguardam a conclusão"
    evidence:
      - ref: "evidence/reproduction.md"
        observation: "operação de 200 ms atrasou heartbeat de 10 ms para 215 ms"
    code_refs:
      - file: "src/telegram/telegram_bot.py"
        symbol: "TelegramBot.listar_compras e handlers equivalentes"
        commit: null
  reproduction_tests: ["tests/test_bot_responsiveness.py::test_listar_compras_nao_bloqueia_event_loop"]
  regression_tests: ["tests/test_bot_responsiveness.py::test_confirmar_compra_delega_consulta_de_contas"]
spec_verdict: spec-gap
change_set:
  - id: CHG-001
    kind: test
    artifact: tests/test_bot_responsiveness.py
    purpose: "provar bloqueio do event loop e proteger a delegação"
    diff: fix/CHG-001-tests.diff
  - id: CHG-002
    kind: code
    artifact: src/telegram/telegram_bot.py
    purpose: "delegar operações síncronas de banco para threads"
    diff: fix/CHG-002-code.diff
  - id: CHG-003
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20260924-P4TX-v001.md
    purpose: "especificar responsividade do event loop"
    diff: null
closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Operações de banco bloqueiam o event loop do Telegram

## Summary

Handlers assíncronos chamam operações síncronas de banco diretamente, bloqueando outras mensagens enquanto o PostgreSQL responde.

## Expected Behavior

Operações bloqueantes devem sair do event loop. A spec exige consulta financeira sem carregar histórico desnecessário e com comportamento responsivo.

## Actual Behavior

Listagens de compras, contas e categorias, além de etapas de confirmação, acessam o banco diretamente dentro de corrotinas.

## Steps to Reproduce

1. Introduzir latência controlada em uma chamada do banco.
2. Acionar uma listagem ou confirmação.
3. Enviar outra mensagem durante a consulta.
4. Observar que a segunda interação espera o término da primeira.

## Evidence

- `../../../intake/relato-20260924-1646.md`

## Suspected Area

Chamadas de `CompraService` dentro dos handlers de `TelegramBot`.

## Acceptance Criteria

- Operações síncronas de banco executam fora do event loop.
- Uma consulta lenta não impede o processamento de outra interação.
- Testes verificam que os serviços bloqueantes são delegados.
- A suíte existente permanece verde.

## Traceability

- Spec: `_reversa_forward/001-intencoes-financeiras/requirements.md#6-requisitos-não-funcionais`
- Código afetado: `src/telegram/telegram_bot.py`, `src/services/compra_service.py`, `src/database/database.py`

## Resolution

### Causa raiz

Confirmada. Handlers assíncronos chamavam métodos síncronos de banco diretamente, ocupando a thread do event loop durante toda a espera de I/O.

### Veredito da spec

`spec-gap`, aprovado pelo usuário. Adendo: `_reversa_sdd/addenda/bug-BUG-20260924-P4TX-v001.md`.

### Change set

| ID | Tipo | Artefato | Resultado |
|---|---|---|---|
| CHG-001 | test | `tests/test_bot_responsiveness.py` | reprodução determinística e regressão |
| CHG-002 | code | `src/telegram/telegram_bot.py` | 13 operações delegadas para threads |
| CHG-003 | specification | adendo v001 | regra de responsividade formalizada |

### Prova

- Reprodução isolada: heartbeat de 10 ms atrasou para 215 ms.
- Vermelho automatizado: 2 falhas.
- Verde específico: 2 testes aprovados.
- Verde completo: 54 testes aprovados.
- `resolution_kind`: `fixed`.

## Agent Notes

Severidade high e prioridade P1 confirmadas pelo usuário. Taxonomia proposta: área `bot`, módulo `telegram`, feature `responsividade`.

Estratégia direta selecionada pelo usuário. Risco médio por atingir vários handlers, com mudança mecânica e reversível, sem alteração de dados ou contratos.
