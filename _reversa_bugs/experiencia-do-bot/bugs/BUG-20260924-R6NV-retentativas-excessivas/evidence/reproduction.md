# Cápsula de reprodução

## Ambiente

- Data: 2026-09-24
- Sistema: Windows
- Runtime: Python da `.venv`
- Script: `evidence/reproduce_retries.py`
- Provedores simulados, sem tráfego externo

## Procedimento

O cliente Gemini foi configurado para retornar `503 UNAVAILABLE` em todas as chamadas. As esperas foram neutralizadas para medir somente a contagem de tentativas. O Groq retornou sucesso.

## Resultado

- Exit code: 1
- `gemini_calls=9`
- `groq_calls=1`
- Resultado final retornado pelo Groq
- Classificação: deterministic

## Conclusão

`GeminiService` executa três tentativas internas. `IAService` repete o serviço inteiro três vezes, produzindo nove chamadas e esperas acumuladas antes do fallback.

## Prova vermelha automatizada

- Comando: `.venv/Scripts/python.exe -m pytest -q tests/test_ia_failover.py`
- Exit code: 1
- Resultado: 1 falha e 2 testes aprovados
- Falha: esperado 3 chamadas ao Gemini, observado 9
