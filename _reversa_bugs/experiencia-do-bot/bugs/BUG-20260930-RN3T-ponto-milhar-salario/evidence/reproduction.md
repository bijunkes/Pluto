# Cápsula de reprodução

- Data: 2026-09-30
- Commit base: `82e92ca8f7f8108e45b5d15b012c7e7aeda830ea`
- Branch: `develop`
- Ambiente: Windows, Python 3.14.3, ambiente virtual `.venv`
- Comando: `.venv/Scripts/python.exe -c "from src.services.savings_plan_service import SavingsPlanService; print(SavingsPlanService.interpretar_valor('3.800'))"`
- Exit code: `0`
- Resultado observado: `3.80`
- Resultado esperado: `3000.00`
- Taxa: `1/1`
- Classificação: determinístico

## Caminho causal confirmado

O método remove o ponto apenas dentro do ramo condicionado à presença de vírgula. Para `3.800`, o texto permanece inalterado e `Decimal("3.800")` produz `Decimal("3.80")`.
