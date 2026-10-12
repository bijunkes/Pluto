---
schema_version: 1
id: BUG-20260924-R6NV
display_number: 3
title: Retentativas sobrepostas ampliam latência da análise de compra
status: resolved
phase: delivering
severity: medium
priority: P2
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
  classification: environment-dependent
  rate: "reproduzível quando Gemini retorna indisponibilidade"
  suspected_triggers: ["erro 503 do Gemini", "retentativas em duas camadas"]
blocking: []
relationships: []
traceability:
  specs: ["_reversa_forward/001-intencoes-financeiras/requirements.md#6-requisitos-não-funcionais"]
  affected_code: ["src/services/ia_service.py", "src/services/gemini_service.py"]
  root_cause:
    state: confirmed
    hypothesis: "GeminiService e IAService aplicam retentativas independentes à mesma operação"
    causal_path:
      - "Gemini retorna 503"
      - "GeminiService realiza três tentativas"
      - "IAService recebe o erro e repete GeminiService três vezes"
      - "nove chamadas ocorrem antes do fallback para Groq"
    evidence:
      - ref: "evidence/reproduction.md"
        observation: "gemini_calls=9 e groq_calls=1"
    code_refs:
      - file: "src/services/ia_service.py"
        symbol: "IAService.analisar_mensagem"
        commit: null
      - file: "src/services/gemini_service.py"
        symbol: "GeminiService.analisar_mensagem"
        commit: null
  reproduction_tests: ["tests/test_ia_failover.py::test_503_faz_tres_chamadas_totais_antes_do_fallback"]
  regression_tests:
    - "tests/test_ia_failover.py::test_erro_permanente_aciona_fallback_sem_repeticao"
    - "tests/test_ia_failover.py::test_sucesso_do_gemini_nao_chama_groq"
spec_verdict: spec-gap
change_set:
  - id: CHG-001
    kind: test
    artifact: tests/test_ia_failover.py
    purpose: "provar multiplicação de chamadas e proteger o fallback"
    diff: fix/CHG-001-tests.diff
  - id: CHG-002
    kind: code
    artifact: src/services/ia_service.py
    purpose: "remover a camada externa duplicada de retentativas"
    diff: fix/CHG-002-code.diff
  - id: CHG-003
    kind: specification
    artifact: _reversa_sdd/addenda/bug-BUG-20260924-R6NV-v001.md
    purpose: "especificar limite e responsabilidade das retentativas"
    diff: null
closure:
  policy: local-software
  satisfied: true
resolution_kind: fixed
---

# Retentativas sobrepostas ampliam latência da análise de compra

## Summary

O Gemini pode repetir chamadas internamente e voltar a ser repetido pelo serviço de failover, aumentando o tempo até a resposta ou o uso do Groq.

## Expected Behavior

Cada provedor deve ter uma única política de retentativa, com limite previsível e failover rápido quando a indisponibilidade persistir.

## Actual Behavior

`GeminiService` possui até três tentativas para indisponibilidade. `IAService` também repete a chamada até três vezes, multiplicando tentativas e esperas.

## Steps to Reproduce

1. Simular resposta 503 do Gemini.
2. Processar uma compra.
3. Contar chamadas e tempo acumulado antes do fallback.
4. Observar repetição em duas camadas.

## Evidence

- `../../../intake/relato-20260924-1646.md`

## Suspected Area

Política de resiliência em `IAService` e `GeminiService`.

## Acceptance Criteria

- Há somente uma camada responsável pelas retentativas.
- Erros permanentes acionam fallback imediatamente.
- Indisponibilidade temporária respeita número e espera máximos definidos.
- Testes verificam contagem de chamadas e failover.

## Traceability

- Spec: `_reversa_forward/001-intencoes-financeiras/requirements.md#6-requisitos-não-funcionais`
- Código afetado: `src/services/ia_service.py`, `src/services/gemini_service.py`

## Resolution

### Causa raiz

Confirmada. `GeminiService` realizava três tentativas internas e `IAService` repetia o serviço inteiro três vezes, multiplicando a operação para nove chamadas antes do fallback.

### Veredito da spec

`spec-gap`, aprovado pelo usuário. Adendo: `_reversa_sdd/addenda/bug-BUG-20260924-R6NV-v001.md`.

### Change set

| ID | Tipo | Artefato | Resultado |
|---|---|---|---|
| CHG-001 | test | `tests/test_ia_failover.py` | contagem de chamadas e regressão do fallback |
| CHG-002 | code | `src/services/ia_service.py` | removida retentativa externa duplicada |
| CHG-003 | specification | adendo v001 | política única formalizada |

### Prova

- Reprodução isolada: 9 chamadas Gemini e 1 chamada Groq.
- Vermelho automatizado: 1 falha e 2 aprovações.
- Verde específico: 3 testes aprovados.
- Verde completo: 57 testes aprovados.
- Resultado após correção: máximo de 3 chamadas Gemini antes do fallback.
- `resolution_kind`: `fixed`.

## Agent Notes

Severidade medium e prioridade P2 confirmadas pelo usuário. Taxonomia proposta: área `bot`, módulo `services`, feature `failover-ia`.

Risco baixo. A estratégia preserva as três tentativas internas do Gemini e remove apenas a repetição externa da mesma política em `IAService`.
