# Reprodução e validação

## Antes da correção

Comando:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_skill_router.py -q
```

Resultado: `3 failed, 23 passed`. O roteador selecionava `registrar_compra`, nenhum estado de coleta era criado e a mensagem seguinte não consumia esse estado.

## Após a correção

- Testes específicos: `26 passed`.
- Suíte completa: `63 passed, 1 warning`.
- O aviso é uma depreciação preexistente em `google.genai`.
