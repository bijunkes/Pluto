# Lacunas e diagnóstico — roteamento de consultas financeiras

> Revisão baseada no incidente observado em 24/09/2026: a pergunta “quanto eu gastei esse mês?” iniciou indevidamente o cadastro de uma compra de R$ 0,00.

## Diagnóstico causal

### 1. Colisão entre consulta e registro

🟢 **CONFIRMADO** — `RegistrarCompraSkill` aceita qualquer texto que contenha `gastei`, sem exigir produto, valor ou construção afirmativa (`src/telegram/skills/builtin.py:87-96`). A pergunta “quanto eu gastei esse mês?” casa com esse padrão.

🟢 **CONFIRMADO** — `ListarComprasSkill` não reconhece essa formulação: seus padrões exigem verbos como “listar/mostrar/ver/quais” ou expressões como “meus gastos” (`src/telegram/skills/builtin.py:6-15`). Portanto, não há uma candidata de consulta concorrente.

🟢 **CONFIRMADO** — o roteador soma correspondências regex e escolhe a maior pontuação/prioridade, sem considerar negação, interrogação, tempo verbal ou entidades obrigatórias (`src/telegram/skills/base.py:33-35`; `src/telegram/skills/router.py:25-31`).

### 2. O roteamento errado impede a camada capaz de responder

🟢 **CONFIRMADO** — mensagens classificadas como `registrar_compra` são enviadas diretamente ao `CompraService`; somente mensagens sem skill vão para a conversa financeira (`src/telegram/telegram_bot.py:883-919`).

🟢 **CONFIRMADO** — a camada conversacional recebe contexto financeiro, mas o fluxo de registro a ignora (`src/telegram/telegram_bot.py:510-556`).

🟡 **INFERIDO** — se a pergunta chegasse à conversa, ela poderia produzir uma resposta aproximada usando o contexto. Porém, esse contexto contém apenas as últimas 50 compras, não um resumo mensal confiável (`src/services/financial_context_service.py:9-44`).

### 3. O extrator transforma ausência de dados em compra aparentemente válida

🟢 **CONFIRMADO** — os prompts de Gemini e Groq ordenam: produto ausente → “Não informado”; categoria inadequada → “Outros”; valor ausente → `0` (`src/services/gemini_service.py:51-61`; `src/services/groq_service.py:50-60`).

🟢 **CONFIRMADO** — o validador aceita `0`, substitui produto vazio por “Não informado” e categoria desconhecida por “Outros”; não exige valor positivo nem evidência de transação (`src/services/ia_utils.py:64-101`).

🟢 **CONFIRMADO** — qualquer resultado aceito é armazenado como `compra_pendente` e exibido para confirmação (`src/telegram/telegram_bot.py:1002-1024`). Isso explica exatamente os três campos vistos na captura.

## Lacunas de produto e arquitetura

### Consulta mensal não é uma intenção de primeira classe

🔴 **LACUNA** — existe cálculo mensal determinístico em `FinancialSummaryService.calcular_resumo_mensal()` (`src/services/financial_summary_service.py:29-79`), mas não existe uma skill do Telegram que o exponha à frase “quanto eu gastei esse mês?”.

Impacto: uma pergunta central do domínio depende de conversa probabilística ou colide com o cadastro.

### Contrato de registro é permissivo demais

🔴 **LACUNA** — não há contrato explícito dizendo quais evidências mínimas distinguem uma compra de uma consulta. O código aceita uma extração degenerada (`Não informado`, `Outros`, `0`) como sucesso.

Impacto: falsos positivos chegam à confirmação e podem virar registros inválidos.

### Ausência de testes negativos de intenção

🟢 **CONFIRMADO** — os testes cobrem “Gastei R$ 42 no mercado” como registro e frases genéricas como conversa, mas não cobrem pares contrastivos como “gastei R$ 42” versus “quanto gastei?” (`tests/test_skill_router.py:12-33`, `71-97`).

Impacto: a regressão passa pela suíte existente.

### Execução local dos testes está indisponível

🔴 **LACUNA** — nesta revisão, `pytest` não estava no PATH e a `.venv` referenciou `C:\Users\victo\AppData\Local\Programs\Python\Python314\python.exe`, que retornou acesso negado.

Impacto: o diagnóstico está comprovado por rastreamento estático, mas a reprodução automatizada não pôde ser executada neste ambiente.

## Melhorias recomendadas, em ordem

1. **Criar uma intenção determinística de consulta financeira**, por exemplo `consultar_gastos_periodo`, reconhecendo “quanto gastei”, “total gasto”, “gastos deste mês” e variantes, com prioridade superior ao registro e resposta calculada pelo banco.
2. **Tornar o padrão de registro afirmativo e composto**: verbo transacional mais valor explícito, ou verbo mais produto inequívoco; perguntas interrogativas de total não devem casar.
3. **Adicionar validação semântica antes da confirmação**: rejeitar `valor <= 0`, produto ausente e resultados sem evidência suficiente; pedir esclarecimento em vez de criar compra pendente.
4. **Remover o fallback `0` como dado válido** nos extratores. Ausência de valor deve produzir estado “incompleto” ou erro de análise, conforme o próprio prompt conversacional já determina.
5. **Centralizar agregações por período** no serviço determinístico existente, evitando que a LLM some uma janela truncada de 50 itens.
6. **Adicionar testes de contraste e integração** para consulta/registro, incluindo acentos, perguntas, “este mês”, “mês passado” e frases ambíguas.
7. **Adicionar telemetria de decisão**: skill selecionada, padrões que pontuaram e motivo de rejeição do payload, sem registrar conteúdo financeiro sensível.

## Fluxo-alvo

`mensagem → detector de intenção → consulta determinística OU registro → validação de completude → confirmação`

Para “quanto eu gastei esse mês?”: `consultar_gastos_periodo → FinancialSummaryService → resposta com total e período`.

Para “gastei R$ 42 no mercado”: `registrar_compra → extração → validação valor/produto → confirmação`.
