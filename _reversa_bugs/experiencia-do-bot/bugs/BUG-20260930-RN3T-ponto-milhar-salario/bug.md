---
schema_version: 1
id: BUG-20260930-RN3T
display_number: 6
title: Ponto de milhar no salário é interpretado como separador decimal
status: active
phase: patching
severity: medium
priority: P1
created: 2026-09-30
updated: 2026-09-30
origin:
  type: manual-report
  external_ref: null
area: unclassified
module: unclassified
feature: unclassified
labels: [spec-gap, financeiro]
visibility: normal
security_suspected: false
express: true
reproduction:
  classification: deterministic
  rate: "1/1"
  suspected_triggers: ["valor brasileiro com ponto de milhar e sem vírgula decimal"]
blocking: []
relationships: []
traceability:
  specs: []
  affected_code: ["src/services/savings_plan_service.py", "src/telegram/telegram_bot.py"]
  root_cause:
    state: confirmed
    hypothesis: "o parser remove pontos apenas quando a entrada também contém vírgula"
    causal_path:
      - "o usuário informa 3.800"
      - "a entrada não contém vírgula"
      - "o ponto não é removido"
      - "Decimal interpreta 3.800 como o valor decimal 3,8"
      - "o plano é calculado sobre R$ 3,80"
    evidence:
      - ref: "evidence/reproduction.md"
        observation: "a execução isolada retornou Decimal 3.80 para a entrada 3.800"
    code_refs:
      - file: "src/services/savings_plan_service.py"
        symbol: "SavingsPlanService.interpretar_valor"
        commit: "82e92ca8f7f8108e45b5d15b012c7e7aeda830ea"
  reproduction_tests: []
  regression_tests: []
spec_verdict: null
change_risk:
  classification: baixa
  motivos:
    - "mudança localizada no parser do planejamento mensal"
    - "sem alteração de dados persistidos ou contratos externos"
    - "correção reversível e coberta por testes unitários"
change_set:
  - id: CHG-001
    kind: code
    artifact: src/services/savings_plan_service.py
    purpose: "interpretar grupos brasileiros de milhar sem exigir vírgula decimal"
    diff: null
closure:
  policy: local-software
  satisfied: false
resolution_kind: null
---

# Ponto de milhar no salário é interpretado como separador decimal

## Summary

O planejamento mensal interpreta `3.800` como `R$ 3,80`, produzindo todas as parcelas do plano com valores incorretos.

## Expected Behavior

As entradas `3000`, `3.000` e `3.000,00` devem representar `R$ 3.000,00`. Não há especificação formal correspondente, portanto o bug está marcado como `spec-gap`.

## Actual Behavior

A entrada `3.800` representa `R$ 3,80` no resultado do plano.

## Steps to Reproduce

1. Iniciar o planejamento mensal no bot.
2. Informar `3.800` como salário líquido.
3. Observar que o bot apresenta salário líquido de `R$ 3,80`.

## Evidence

- `../../../intake/relato-20260930-1446-salario-com-ponto.md`
- `evidence/reproduction.md`

## Suspected Area

`SavingsPlanService.interpretar_valor`, usado pelo fluxo de planejamento em `TelegramBot._continuar_planejamento_economia`.

## Acceptance Criteria

- `3000`, `3.000` e `3.000,00` resultam em `Decimal("3000.00")`.
- `3.800` gera um plano com salário formatado como `R$ 3.800,00`.
- Formatos brasileiros com centavos continuam funcionando.
- Entradas inválidas ou não positivas continuam rejeitadas.
- A suíte de testes permanece verde.

## Traceability

- Spec: `spec-gap`.
- Código afetado: `src/services/savings_plan_service.py` e fluxo consumidor em `src/telegram/telegram_bot.py`.
- Testes relacionados: `tests/test_savings_plan_service.py`.

## Resolution

A correção de código foi aplicada em `SavingsPlanService.interpretar_valor`. Grupos com ponto e exatamente três dígitos passam a ser tratados como milhares, enquanto formatos decimais com um ou dois dígitos após o ponto permanecem inalterados.

O usuário solicitou explicitamente que nenhum teste fosse criado ou executado. Por isso, a prova de regressão, o veredito de especificação e o fechamento pela política `local-software` permanecem pendentes.

## Agent Notes

Severidade `medium` e prioridade `P1` assumidas na rota expressa devido ao cálculo financeiro incorreto e à correção localizada. Taxonomia sugerida: área `bot`, módulo `planejamento-financeiro`, feature `plano-50-30-20`.

O formato com ponto e um ou dois dígitos à direita permanece ambíguo. A correção proposta reconhece como milhar apenas grupos brasileiros válidos de três dígitos, preservando entradas decimais como `3.80` conforme o comportamento atual.
