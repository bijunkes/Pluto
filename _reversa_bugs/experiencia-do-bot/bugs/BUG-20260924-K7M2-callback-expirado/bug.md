---
schema_version: 1
id: BUG-20260924-K7M2
display_number: 1
title: Callback expirado encerra interação sem resposta útil
status: resolved
phase: delivering
severity: high
priority: P1
created: 2026-09-24
updated: 2026-09-24
origin:
  type: manual-report
  external_ref: null
area: unclassified
module: unclassified
feature: unclassified
labels: []
visibility: normal
security_suspected: false
reproduction:
  classification: environment-dependent
  rate: "1 ocorrência confirmada"
  suspected_triggers: ["pressionar botão inline após expiração do callback"]
blocking: []
relationships:
  - bug: BUG-20260924-P4TX
    type: related-to
    state: proposed
    evidence: []
traceability:
  specs: ["_reversa_forward/001-intencoes-financeiras/requirements.md#7-critérios-de-aceitação"]
  affected_code: ["src/telegram/telegram_bot.py"]
  root_cause:
    state: confirmed
    hypothesis: "menu_callback retorna imediatamente quando query.answer falha por expiração"
    causal_path:
      - "usuário pressiona botão antigo"
      - "Telegram rejeita query.answer"
      - "except captura a exceção"
      - "return encerra o handler sem mensagem"
    evidence:
      - ref: "evidence/reproduction.md"
        observation: "reprodução isolada concluiu com edit_calls=0"
    code_refs:
      - file: "src/telegram/telegram_bot.py"
        symbol: "TelegramBot.menu_callback"
        commit: null
  reproduction_tests: ["tests/test_callback_handling.py::test_callback_expirado_orienta_usuario_sem_executar_acao"]
  regression_tests:
    - "tests/test_callback_handling.py::test_callback_valido_continua_executando_acao"
    - "tests/test_callback_handling.py::test_erro_inesperado_do_callback_nao_e_silenciado"
spec_verdict: spec-gap
change_set:
  - id: CHG-001
    kind: test
    artifact: tests/test_callback_handling.py
    purpose: "provar a falha e proteger callbacks válidos, expirados e erros inesperados"
    diff: fix/CHG-001-tests.diff
  - id: CHG-002
    kind: code
    artifact: src/telegram/telegram_bot.py
    purpose: "centralizar o tratamento seguro de callbacks"
    diff: fix/CHG-002-code.diff
  - id: CHG-003
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20260924-K7M2-v001.md
    purpose: "especificar pela primeira vez o comportamento de callback expirado"
    diff: null
closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Callback expirado encerra interação sem resposta útil

## Summary

Botões antigos podem produzir `Query is too old and response timeout expired or query id is invalid`, encerrando o fluxo ou deixando o usuário sem orientação.

## Expected Behavior

A interação deve tolerar callbacks expirados e orientar o usuário a abrir um menu atualizado. A spec efetiva exige resposta observável e ausência de travamento no fluxo financeiro.

## Actual Behavior

O menu captura a exceção e retorna sem resposta. Outros callbacks não tratam a exceção de `query.answer()`.

## Steps to Reproduce

1. Abrir uma mensagem com botão inline.
2. Aguardar até o callback expirar.
3. Pressionar o botão antigo.
4. Observar o erro e a ausência de continuidade.

## Evidence

- `../../../intake/relato-20260924-1646.md`

## Suspected Area

Handlers de callback em `src/telegram/telegram_bot.py`.

## Acceptance Criteria

- Callback expirado não interrompe o processo com exceção não tratada.
- O bot envia orientação usando um canal ainda válido quando possível.
- Todos os handlers usam a mesma política de resposta segura.
- Testes cobrem callback válido e expirado.

## Traceability

- Spec: `_reversa_forward/001-intencoes-financeiras/requirements.md#7-critérios-de-aceitação`
- Código afetado: `src/telegram/telegram_bot.py`

## Resolution

### Causa raiz

Confirmada. `menu_callback` capturava qualquer exceção de `query.answer()` e retornava sem resposta. Os demais handlers não compartilhavam uma política segura.

### Veredito da spec

`spec-gap`, aprovado pelo usuário. Adendo: `_reversa_sdd/addenda/bug-BUG-20260924-K7M2-v001.md`.

### Change set

| ID | Tipo | Artefato | Resultado |
|---|---|---|---|
| CHG-001 | test | `tests/test_callback_handling.py` | prova vermelho e regressão |
| CHG-002 | code | `src/telegram/telegram_bot.py` | tratamento centralizado e seguro |
| CHG-003 | specification | adendo v001 | comportamento formalizado |

### Prova

- Vermelho: 2 falhas e 1 aprovação antes da correção.
- Verde específico: 3 testes aprovados.
- Verde completo: 52 testes aprovados.
- `resolution_kind`: `fixed`.

## Agent Notes

Severidade high e prioridade P1 confirmadas pelo usuário. Taxonomia proposta: área `bot`, módulo `telegram`, feature `callbacks`.

Estratégia direta selecionada pelo usuário. Risco da mudança classificado como médio porque a política será centralizada e aplicada a múltiplos handlers de callback, sem alteração de dados ou contratos externos.
