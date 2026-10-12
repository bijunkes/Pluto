# Evidência de reprodução

Data: 2026-09-24

Comando executado na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -c "import debugpy"
```

Resultado:

```text
ModuleNotFoundError: No module named 'debugpy'
```

Código de saída: `1`.

A configuração `.vscode/launch.json` declara `"type": "debugpy"`, enquanto `requirements-dev.txt` contém somente a referência às dependências de produção e `pytest`.

## Prova automatizada

Antes da correção:

```text
3 failed in 0.24s
```

Após a correção:

```text
debugpy 1.8.22
3 passed in 0.03s
60 passed, 1 warning in 4.14s
```
