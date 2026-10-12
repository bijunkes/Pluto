---
schema_version: 1
id: BUG-20260924-C3WP
display_number: 5
title: Intenção de iniciar registro é tratada como compra incompleta
status: active
phase: validating
severity: medium
priority: P1
created: 2026-09-24
updated: 2026-09-24
origin:
  type: manual-report
  external_ref: null
area: unclassified
module: unclassified
feature: unclassified
labels: [spec-gap]
visibility: normal
security_suspected: false
express: true
reproduction:
  classification: deterministic
  rate: "1/1"
  suspected_triggers: ["frase de intenção contém a palavra compra"]
blocking: []
relationships: []
traceability:
  specs: ["_reversa_forward/001-intencoes-financeiras/requirements.md#3-regras-de-negócio"]
  affected_code: ["src/telegram/skills/builtin.py", "src/telegram/telegram_bot.py"]
  root_cause:
    state: confirmed
    hypothesis: "o roteador não separava intenção de iniciar o fluxo da descrição de uma compra"
    causal_path:
      - "a expressão contém a palavra compra"
      - "RegistrarCompraSkill é selecionada"
      - "a frase é enviada imediatamente ao CompraService"
      - "a extração falha porque produto e valor não foram informados"
    evidence:
      - ref: "evidence/reproduction.md"
        observation: "três testes falharam antes da correção e passaram depois"
    code_refs:
      - file: "src/telegram/skills/builtin.py"
        symbol: "RegistrarCompraSkill"
        commit: null
      - file: "src/telegram/telegram_bot.py"
        symbol: "TelegramBot._receber_compra_ou_conversa"
        commit: null
  reproduction_tests: ["tests/test_skill_router.py::test_pedido_para_registrar_compra_solicita_descricao"]
  regression_tests:
    - "tests/test_skill_router.py::test_descricao_seguinte_e_analisada_como_compra"
    - "tests/test_skill_router.py::test_compra_explicita_continua_no_registro"
spec_verdict: pending
change_set:
  - id: CHG-001
    kind: test
    artifact: tests/test_skill_router.py
    purpose: "proteger a separação entre intenção e descrição"
    diff: fix/CHG-001-tests.diff
  - id: CHG-002
    kind: code
    artifact: "src/telegram/skills/builtin.py e src/telegram/telegram_bot.py"
    purpose: "criar skill de início e manter estado até a descrição"
    diff: fix/CHG-002-code.diff
closure:
  policy: local-software
  satisfied: false
resolution_kind: null
---

# Intenção de iniciar registro é tratada como compra incompleta

## Expected Behavior

Uma solicitação como `quero registrar uma compra` inicia o fluxo e pede a descrição. Uma compra já completa continua sendo analisada diretamente.

## Actual Behavior

A solicitação era enviada à IA como se já fosse a descrição completa da compra.

## Resolution progress

- Causa raiz confirmada.
- Prova vermelha: 3 falhas e 23 aprovações.
- Prova verde específica: 26 aprovações.
- Suíte completa: 63 aprovações e um aviso preexistente.
- Veredito documental pendente.

## Agent Notes

Severidade medium e prioridade P1 assumidas na rota expressa. Risco baixo: mudança restrita ao roteamento e ao estado conversacional. Taxonomia sugerida: área `bot`, módulo `telegram`, feature `registro-guiado-de-compra`.
