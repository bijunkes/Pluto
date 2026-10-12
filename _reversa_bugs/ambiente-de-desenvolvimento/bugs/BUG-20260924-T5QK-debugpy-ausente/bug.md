---
schema_version: 1
id: BUG-20260924-T5QK
display_number: 4
title: Ambiente de depuração não possui debugpy
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
  rate: "1/1 no ambiente virtual atual"
  suspected_triggers: ["debugpy ausente da .venv", "interpretador não fixado na configuração do workspace"]
blocking: []
relationships: []
traceability:
  specs: []
  affected_code: [".vscode/launch.json", ".vscode/settings.json", ".vscode/extensions.json", "requirements-dev.txt", "pytest.ini"]
  root_cause:
    state: confirmed
    hypothesis: "a configuração usa o adaptador debugpy, mas a dependência não está declarada nem instalada no ambiente virtual do projeto"
    causal_path:
      - "o VS Code seleciona a configuração Pluto: iniciar bot"
      - "a configuração solicita o tipo debugpy"
      - "o workspace não fixa explicitamente o interpretador da .venv"
      - "a .venv atual não consegue importar debugpy"
      - "a sessão de depuração não é iniciada"
    evidence:
      - ref: "evidence/reproduction.md"
        observation: "o import de debugpy termina com ModuleNotFoundError"
    code_refs:
      - file: ".vscode/launch.json"
        symbol: "Pluto: iniciar bot"
        commit: null
      - file: "requirements-dev.txt"
        symbol: "dependências de desenvolvimento"
        commit: null
  reproduction_tests: ["tests/test_debug_configuration.py::test_debugpy_esta_declarado_nas_dependencias_de_desenvolvimento"]
  regression_tests:
    - "tests/test_debug_configuration.py::test_launch_usa_interpretador_do_ambiente_virtual"
    - "tests/test_debug_configuration.py::test_extensoes_de_python_sao_recomendadas"
spec_verdict: pending
change_set:
  - id: CHG-001
    kind: test
    artifact: tests/test_debug_configuration.py
    purpose: "provar a configuração incompleta e evitar regressão"
    diff: fix/CHG-001-tests.diff
  - id: CHG-002
    kind: configuration
    artifact: ".vscode e requirements-dev.txt"
    purpose: "fixar a .venv, declarar debugpy e recomendar as extensões necessárias"
    diff: fix/CHG-002-config.diff
closure:
  policy: local-software
  satisfied: false
resolution_kind: null
---

# Ambiente de depuração não possui debugpy

## Summary

A configuração do VS Code solicita `debugpy`, mas o ambiente de desenvolvimento não declara essa dependência, não recomenda as extensões correspondentes e não fixa o interpretador da `.venv`.

## Expected Behavior

Ao selecionar `Pluto: iniciar bot`, o VS Code deve usar a `.venv` do projeto e iniciar `main` com o depurador Python.

## Actual Behavior

A depuração não inicia. A reprodução direta no mesmo ambiente falha ao importar `debugpy`.

## Steps to Reproduce

1. Abrir o projeto no VS Code.
2. Selecionar `Pluto: iniciar bot`.
3. Iniciar a depuração.
4. Alternativamente, executar `.\.venv\Scripts\python.exe -c "import debugpy"`.
5. Observar que o adaptador não está disponível no ambiente virtual atual.

## Evidence

- `../../../intake/relato-20260924-debug-vscode.md`
- `evidence/reproduction.md`

## Acceptance Criteria

- `debugpy` está declarado nas dependências de desenvolvimento e instalado na `.venv`.
- O workspace usa explicitamente o Python da `.venv`.
- As extensões Python e Python Debugger são recomendadas pelo workspace.
- Os testes de configuração passam.
- O comando de importação de `debugpy` passa no ambiente virtual.

## Agent Notes

Risco baixo. A mudança é restrita ao ambiente de desenvolvimento e não altera o comportamento do bot em produção. Taxonomia sugerida: área `developer-experience`, módulo `vscode`, feature `debug-local`.

O estado da extensão instalada no VS Code não pôde ser confirmado pelo CLI porque o executável tentou escrever em uma pasta de perfil sem permissão. Isso não invalida a falha determinística da `.venv`, mas será necessário confirmar visualmente a extensão se o VS Code ainda não iniciar após a correção.

## Validation

- Vermelho: `3 failed` antes da alteração de configuração.
- Dependência instalada: `debugpy 1.8.22`.
- Verde específico: `3 passed`.
- Verde completo: `60 passed`, com um aviso de depreciação preexistente em `google.genai`.
- Veredito de especificação: aguardando confirmação do usuário.
