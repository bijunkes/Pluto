# Relatório de Confiança — Projeto-Final-Entra21

> Gerado pelo Reviewer em 24/09/2026. Escopo focal: incidente de roteamento “quanto eu gastei esse mês?”.

## Resumo geral

| Nível | Quantidade | Percentual |
|---|---:|---:|
| 🟢 CONFIRMADO | 9 | 75% |
| 🟡 INFERIDO | 1 | 8% |
| 🔴 LACUNA | 2 | 17% |
| **Total** | **12** | **100%** |

**Confiança geral:** 79% — `(9 + 1 × 0,5) / 12`.

## Por área revisada

| Área | 🟢 | 🟡 | 🔴 | Confiança |
|---|---:|---:|---:|---:|
| Roteamento de skills | 4 | 0 | 1 | 80% |
| Extração e validação de compra | 3 | 0 | 1 | 75% |
| Conversa e contexto financeiro | 1 | 1 | 0 | 75% |
| Cobertura de testes | 1 | 0 | 0 | 100% |

## Conclusão

O problema não é primariamente “a IA estar burra”. A decisão errada ocorre antes da IA conversacional: a regex de registro captura a palavra `gastei`, envia a pergunta ao extrator de compras e o contrato permissivo converte campos ausentes em valores-padrão válidos. O comportamento da captura é, portanto, consequência determinística do fluxo atual.

## Lacunas pendentes

- Não há uma skill/contrato específico para consulta agregada por período no Telegram.
- Não está especificado o conjunto mínimo de evidências para que uma mensagem possa virar compra pendente.
- A suíte não pôde ser executada por inconsistência no ambiente Python local; detalhes em `gaps.md`.

## Recomendações

- [ ] Implementar consulta determinística por período antes de ampliar prompts.
- [ ] Endurecer roteamento e validação de compras.
- [ ] Cobrir pares contrastivos consulta versus registro.
- [ ] Reparar/recriar a `.venv` e executar a suíte completa.

## Histórico de reclassificações

Nenhuma spec canônica foi reclassificada: `_reversa_sdd` ainda não contém units com `requirements.md`, `design.md` e `tasks.md`.

## Revisão cruzada

- Revisão cruzada realizada: não.
- Motivo: não há ferramenta externa `codex:*` disponível na sessão e as specs canônicas ainda não foram geradas.
