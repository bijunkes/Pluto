# Registro de Bugs (Reversa Bugs)

> Gerado pelo Reversa em 2026-09-24. Este arquivo é o contrato do registro de bugs deste projeto.
> Source of truth: cada `<contexto>/bugs/<ID>/bug.md`. Tudo em `generated/` é projeção regenerável.

## Configuração do projeto

```yaml
closure_policy: local-software
control_mode: gated
```

Um bug é considerado resolvido quando os testes de regressão passam e o veredito da spec está registrado. Aplicação de testes, change sets e alterações de spec exigem os gates do corretor.

## Estrutura

Os bugs são agrupados por contexto em `_reversa_bugs/<contexto>/`. Cada pasta de bug é imutável quanto ao endereço e contém o registro canônico, evidências e artefatos da correção.

## Ciclo de vida

`status`: `open` para `active` para `resolved`. Bloqueios são condições, não status. Ao satisfazer a política de fechamento, o bug recebe `DONE.md` e passa a ser somente leitura.

## Rastreabilidade obrigatória

Todo bug deve ligar comportamento esperado, código afetado, causa raiz confirmada e testes de reprodução e regressão. Bugs sem spec recebem o label `spec-gap`.

## Convenções

- ID: `BUG-<YYYYMMDD>-<sufixo>`.
- `display_number` é um apelido humano global.
- Evidências ficam em `evidence/`.
- Views em `generated/` são regeneráveis.
