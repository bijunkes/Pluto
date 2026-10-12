---
schema_version: 1
id: BUG-20261001-SFQC
display_number: 7
title: Falar com Pluto exige entrevista antes da conversa
status: active
phase: testing
severity: medium
priority: P1
created: 2026-10-01
updated: 2026-10-01
express: true
origin: {type: manual-report, external_ref: null}
area: unclassified
module: unclassified
feature: unclassified
labels: [spec-gap]
visibility: normal
security_suspected: false
reproduction: {classification: not-reproduced, rate: null}
blocking: []
relationships: []
traceability:
  specs: []
  affected_code: [src/telegram/telegram_bot.py, src/services/conversation_service.py]
  root_cause:
    state: supported
    hypothesis: Ausência de perfil inicia entrevista obrigatória e desvia mensagens da conversa.
    evidence:
      - ref: evidence/reproduction.md
        observation: Caminho causal verificado por leitura; runtime indisponível.
  reproduction_tests:
    - fix/proposed/test_skill_router.py::test_falar_com_pluto_abre_conversa_sem_entrevista
    - fix/proposed/test_skill_router.py::test_pergunta_geral_e_respondida_sem_renda
  regression_tests:
    - fix/proposed/test_skill_router.py::test_pedido_de_plano_continua_solicitando_salario
spec_verdict: null
change_set:
  - {id: CHG-001, kind: code, artifact: src/telegram/telegram_bot.py, diff: fix/CHG-001-code.diff}
  - {id: CHG-002, kind: code, artifact: src/services/conversation_service.py, diff: fix/CHG-002-code.diff}
  - {id: CHG-003, kind: test, artifact: tests/test_skill_router.py, diff: fix/CHG-003-tests.diff}
closure: {policy: local-software, satisfied: false}
resolution_kind: null
---

# Falar com Pluto exige entrevista antes da conversa

## Summary
Conversa condicionada ao cadastro financeiro.

## Expected Behavior
Spec-gap: não localizada spec efetiva deste comportamento. O usuário definiu conversa direta e entrevista apenas quando necessária ao pedido.

## Actual Behavior
Sem perfil, o botão inicia três perguntas; mensagens seguintes alimentam o questionário.

## Steps to Reproduce
1. Entrar sem perfil financeiro.
2. Clicar em Falar com Pluto.
3. Perguntar o que são juros compostos.
4. Observar avanço da entrevista em vez da resposta.

## Evidence
- [Relato](../../intake/relato-20261001-151415.md)
- [Diagnóstico](evidence/reproduction.md)

## Suspected Area
Entrada do modo conversa e interceptação por entrevista_financeira.

## Acceptance Criteria
- Abrir conversa sem entrevista, preservando perfil existente.
- Estado antigo não captura novas perguntas.
- Planejamento solicitado continua pedindo salário.
- IA pergunta somente dados necessários, permite recusa e mudança de assunto.

## Traceability
Propostas completas e diffs em fix/. CHG-001, CHG-002 e CHG-003 aplicados após aprovação explícita do usuário: aplicar.

## Resolution
Patch aprovado pelo usuário e aplicado. git diff --check passou. Tentativa de pytest após aplicar os testes retornou exit code 1: interpretador Python314 inacessível. Validação funcional permanece pendente; bug não encerrado.
Veredito recomendado: spec-gap, pendente de decisão humana.
Não houve execução de testes; entrevista contextual via IA também exige validação manual.

## Agent Notes
Severidade medium e prioridade P1 propostas pelo agente. Risco baixo, sem migração.
Registro mínimo e preparação conforme pedido de ajuste; gates de aplicação preservados.
Taxonomia vazia: unclassified. Não alterar savings_plan_service.py, que já tem mudança local.
Views pendentes de fechamento. Nenhum DONE.md criado.