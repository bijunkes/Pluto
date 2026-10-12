# Relato: salário com ponto interpretado como valor decimal

Data: 2026-09-30 14:46
Contexto: experiência do bot
Origem: relato manual com captura de tela anexada na conversa

## Palavras do usuário

> quando insere o valor, com tipo 3000 mas ele não entende: olhe

Na captura, o usuário informa `3.800` como salário líquido. O bot responde com salário líquido de `R$ 3,80`, necessidades de `R$ 1,90`, gastos flexíveis de `R$ 1,14` e valor para guardar de `R$ 0,76`.

## Comportamento esperado

No contexto monetário brasileiro, a entrada `3.800` deve ser interpretada como `R$ 3.800,00`. As entradas `3000`, `3.000` e `3.000,00` devem produzir o mesmo valor.

## Comportamento observado

A entrada `3.800` é interpretada como o decimal `3.80`.

## Diagnóstico inicial

Em `src/services/savings_plan_service.py`, `SavingsPlanService.interpretar_valor` remove pontos apenas quando a entrada também contém vírgula. Sem vírgula, `Decimal("3.800")` é avaliado como 3,8.

Os testes existentes cobrem `R$ 3.000,00`, `2500` e `1.234,56 reais`, mas não cobrem o formato brasileiro com separador de milhar e sem centavos, como `3.000`.

## Evidência

A captura de tela foi fornecida diretamente na conversa e não possui caminho local disponível para cópia. O conteúdo visual relevante está transcrito acima.
