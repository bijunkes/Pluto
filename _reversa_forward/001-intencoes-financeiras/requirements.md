# Requirements: Intenções financeiras e validação de compras

> Identificador: `001-intencoes-financeiras`
> Data: `2026-09-24`
> Pasta da extração reversa: `_reversa_sdd/`
> Confiança: 🟢 CONFIRMADO, 🟡 INFERIDO, 🔴 LACUNA / DÚVIDA

## 1. Resumo executivo

A feature deve distinguir consultas sobre gastos já registrados de mensagens que comunicam uma nova compra. O usuário do bot deve conseguir perguntar quanto gastou no mês e receber um total calculado sobre seus dados, sem abrir o fluxo de confirmação de compra. Mensagens de compra incompletas não devem gerar registros pendentes com produto genérico ou valor zero.

## 2. Contexto a partir do legado

| Fonte | Trecho relevante | Confiança |
|-------|------------------|-------------|
| `_reversa_sdd/inventory.md#Estrutura` | O bot, o roteador e os serviços financeiros são componentes separados do sistema. | 🟢 |
| `_reversa_sdd/gaps.md#Diagnóstico causal` | A palavra “gastei” captura perguntas de consulta e as envia ao cadastro. | 🟢 |
| `_reversa_sdd/gaps.md#O extrator transforma ausência de dados em compra aparentemente válida` | Produto, categoria e valor ausentes recebem fallbacks aceitos pelo validador. | 🟢 |
| `_reversa_sdd/gaps.md#Melhorias recomendadas, em ordem` | Recomenda intenção determinística de consulta, validação estrita e testes contrastivos. | 🟢 |

## 3. Personas e cenários de uso

| Persona | Objetivo | Cenário-chave |
|---------|----------|---------------|
| Usuário do Pluto | Consultar seu gasto mensal | Pergunta “quanto eu gastei esse mês?” e recebe o total do período. |
| Usuário do Pluto | Registrar uma compra real | Informa produto e valor e recebe uma confirmação antes do salvamento. |
| Usuário do Pluto | Corrigir uma mensagem incompleta | Informa uma compra sem valor e recebe pedido de complemento, não uma compra de R$ 0,00. |

## 4. Regras de negócio novas ou alteradas

1. **RN-01:** Perguntas sobre totais ou gastos em um período são consultas, ainda que contenham verbos também usados no registro, como “gastei”. 🟢
   - Tipo: alterada
2. **RN-02:** Consultas do mês atual usam o início do mês local até o instante da consulta e somam apenas compras do usuário. 🟢
   - Tipo: nova
3. **RN-03:** Uma compra pendente só pode ser criada quando houver produto identificável e valor numérico estritamente maior que zero. 🟡
   - Tipo: alterada
4. **RN-04:** Mensagens incompletas devem pedir esclarecimento e não usar `Não informado`, `Outros` e `0` como se fossem uma compra válida. 🟢
   - Tipo: alterada
5. **RN-05:** O resultado financeiro exibido ao usuário deve ser calculado deterministicamente a partir do banco, não pela soma livre de uma resposta de modelo de linguagem. 🟢
   - Tipo: nova

## 5. Requisitos Funcionais

| ID | Requisito | Prioridade | Critério de aceite | Confiança |
|----|-----------|------------|--------------------|-------------|
| RF-01 | Identificar perguntas de total gasto no mês atual como consulta financeira. | Must | “Quanto eu gastei esse mês?” não chama o analisador de compra nem cria `compra_pendente`. | 🟢 |
| RF-02 | Responder a consulta mensal com o total calculado para o usuário e o período correspondente. | Must | A resposta contém o total em reais e identifica o mês consultado. | 🟢 |
| RF-03 | Manter o registro de mensagens afirmativas com produto e valor. | Must | “Gastei R$ 42 no mercado” continua abrindo a confirmação com produto e valor. | 🟢 |
| RF-04 | Rejeitar a confirmação automática de uma extração com valor zero, negativo ou produto ausente. | Must | Nenhum desses resultados é salvo em `compra_pendente`; o usuário recebe pedido para informar produto e valor. | 🟢 |
| RF-05 | Cobrir por testes frases contrastivas de consulta e registro. | Must | A suíte contém casos para mês atual, pergunta genérica de gasto, compra válida e compra sem valor. | 🟢 |
| RF-06 | Preservar o comportamento das demais skills e estados prioritários. | Should | Os testes existentes de conta, categoria, dashboard, ajuda e planejamento continuam passando. | 🟡 |

## 6. Requisitos Não Funcionais

| Tipo | Requisito | Evidência ou justificativa | Confiança |
|------|-----------|----------------------------|-------------|
| Correção | A soma mensal deve usar o serviço financeiro e os filtros do banco. | Evita resultados probabilísticos e janelas truncadas. | 🟢 |
| Segurança | Toda consulta deve permanecer vinculada ao identificador do usuário corrente. | O banco do legado é instanciado por usuário. | 🟢 |
| Desempenho | A consulta deve executar uma única leitura agregada ou uma listagem limitada ao período. | Evita carregar histórico desnecessário. | 🟡 |
| Observabilidade | Falhas de análise devem indicar o estágio do fluxo sem registrar dados financeiros completos. | Necessário para diagnosticar roteamento sem expor conteúdo sensível. | 🟡 |
| Compatibilidade | A resposta deve manter pt-BR e formatação monetária brasileira. | Interface atual do bot. | 🟢 |

## 7. Critérios de Aceitação

```gherkin
Cenário: Consultar o total gasto no mês atual
  Dado um usuário com compras registradas no mês atual
  Quando ele enviar “quanto eu gastei esse mês?”
  Então o bot responderá o total em reais referente ao mês atual
  E não criará uma compra pendente

Cenário: Consultar um mês sem compras
  Dado um usuário sem compras no mês atual
  Quando ele perguntar quanto gastou neste mês
  Então o bot responderá R$ 0,00 de forma informativa
  E não oferecerá confirmação de compra

Cenário: Registrar compra explícita
  Dado um usuário fora de outro fluxo prioritário
  Quando ele enviar “gastei R$ 42 no mercado”
  Então o bot analisará a nova compra
  E exibirá a confirmação com valor maior que zero

Cenário: Mensagem de compra sem valor
  Dado um usuário fora de outro fluxo prioritário
  Quando ele informar uma compra sem um valor identificável
  Então o bot pedirá produto e valor
  E não armazenará uma compra pendente com valor zero

Cenário: Resultado inválido retornado pelo analisador
  Dado que o analisador retorne produto ausente ou valor menor ou igual a zero
  Quando o resultado for validado
  Então o fluxo será interrompido com erro de análise recuperável
  E nenhuma confirmação será exibida
```

## 8. Prioridade MoSCoW

| Item | MoSCoW | Justificativa |
|------|--------|---------------|
| RF-01 | Must | Corrige a causa direta do incidente. |
| RF-02 | Must | Entrega a intenção real do usuário. |
| RF-03 | Must | Impede regressão do cadastro principal. |
| RF-04 | Must | Evita dados inválidos e confirmações enganosas. |
| RF-05 | Must | Protege a correção contra regressões. |
| RF-06 | Should | Mantém compatibilidade do restante do bot. |
| RNF de observabilidade | Should | Facilita diagnóstico posterior sem bloquear a correção. |

## 9. Esclarecimentos

> Nenhuma sessão de dúvidas registrada. Os critérios necessários à primeira implementação foram definidos a partir do incidente e do código existente.

## 10. Lacunas

- Nenhuma lacuna bloqueante para a primeira entrega. Consultas de mês passado e períodos arbitrários ficam fora do escopo inicial e podem ser adicionadas posteriormente.

## 11. Histórico de alterações

| Data | Alteração | Autor |
|------|-----------|-------|
| 2026-09-24 | Versão inicial gerada por `/reversa-requirements` | reversa |
