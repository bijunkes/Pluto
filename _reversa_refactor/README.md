# Registro de Qualidade de Código (Reversa Refactor)

> GENERATED / MANAGED pelo time Code Quality do Reversa. Este README guarda as políticas do registro.
> As pastas de contexto e os artefatos de transformação nascem sob demanda.

## Políticas

Escolhas confirmadas pelo usuário em 2026-09-17: `gated` e `require-characterization`.

- `control_mode`: gated
  - `gated` (padrão): leitura, análise, medição e prova de comportamento fluem sem aprovação. Todo passo que toca o código do projeto passa por gate com diff aprovado.
  - `supervised`: o agente pode aplicar transformações de baixo risco já provadas, avisando; alto risco continua com gate.
  - `autonomous`: aplica automaticamente o que estiver verde e provado. Mesmo aqui têm gate obrigatório: remover código, alterar spec efetiva, enviar material a harness externo, operação destrutiva.
- `safety_net_policy`: require-characterization
  - `require-characterization` (padrão): transformação que altera estrutura ou lógica exige rede de segurança (testes existentes + caracterização) verde antes e depois.
  - `allow-unproven`: permite transformação sem rede, sempre rebaixada para vermelho e marcada como sem prova mecânica no registro.

## Invariante do registro

Nenhuma transformação altera comportamento observável. O que não prova preservação, para no gate. Toda transformação aplicada é reversível pelo diff guardado.

## Estrutura

```
_reversa_refactor/
  README.md
  <contexto>/
    opportunities/
    transformations/
      OPP-<data>-<sufixo>-<slug>/
        plan.html
        safety-net/
        before-after/
        CHG-NNN.diff
        transformation.md
    generated/
```
