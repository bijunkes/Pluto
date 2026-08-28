# Pluto API

Backend HTTP compartilhado entre o bot do Telegram e o dashboard web.
Expõe a mesma lógica de negócio que já existia (`CompraService`,
`Database`) como endpoints REST, além de importação de CSV e do login
via link do bot.

## Como rodar

```bash
pip install -r requirements.txt --break-system-packages
cp .env.example .env   # preencha TELEGRAM_BOT_TOKEN, GEMINI_API_KEY e AUTH_SECRET_KEY
uvicorn src.api.main:app --reload --port 8000
```

A API serve o dashboard estático (pasta `dashboard/`) na raiz, então
com o comando acima tanto a API quanto o dashboard já ficam
disponíveis em `http://localhost:8000`. A documentação interativa da
API (gerada pelo FastAPI) fica em `http://localhost:8000/docs`.

Rode o bot em paralelo (outro terminal), usando o mesmo `.env`:

```bash
python -m src.telegram.telegram_bot
```

## Login (link mágico)

1. O usuário manda `/dashboard` pro bot.
2. O bot gera um link assinado e de curta duração (chave
   `AUTH_SECRET_KEY`, válido por 5 minutos — ver
   `src/services/auth_service.py`) e manda um botão "Abrir Dashboard".
3. O navegador abre `login.html?token=...`, que troca o token por uma
   sessão em `POST /auth/sessao`. A API grava um cookie httpOnly
   (`pluto_session`, válido por 30 dias) e o dashboard passa a chamar
   as rotas normalmente com esse cookie.
4. Todas as rotas `/usuarios/{usuario_id}/...` exigem esse cookie e
   conferem que o `usuario_id` autenticado é o mesmo da URL — ninguém
   acessa os dados de outra pessoa, mesmo trocando o ID manualmente.

## Endpoints

| Método | Rota | Descrição | Autenticado? |
|--------|------|-----------|:---:|
| POST | `/auth/sessao` | Troca o token do link mágico por uma sessão | — |
| GET | `/auth/me` | Devolve o usuário da sessão atual | ✅ |
| POST | `/auth/logout` | Encerra a sessão (apaga o cookie) | — |
| GET | `/usuarios/{usuario_id}/compras` | Lista as compras do usuário | ✅ |
| POST | `/usuarios/{usuario_id}/compras` | Cria uma compra manualmente (sem IA) | ✅ |
| GET | `/usuarios/{usuario_id}/categorias` | Lista as categorias do usuário | ✅ |
| POST | `/usuarios/{usuario_id}/categorias` | Cria uma nova categoria | ✅ |
| POST | `/usuarios/{usuario_id}/compras/importar-csv` | Importa compras a partir de um arquivo CSV | ✅ |
| GET | `/usuarios/{usuario_id}/saude` | Healthcheck / inicializa o banco do usuário | ✅ |

"Autenticado" quer dizer: exige o cookie `pluto_session` válido, e o
`usuario_id` da URL precisa bater com o da sessão (senão, `403`).

## Importação de CSV

O CSV aceita variações comuns de nome de coluna:

- Produto: `produto`, `item`, `descricao`, `nome`
- Categoria: `categoria`, `tipo` (opcional — cai em "Outros" se ausente)
- Valor: `valor`, `preco`, `price`, `total`

Valores em formato brasileiro são aceitos (`"R$ 129,90"`, `"1.234,56"`).

Categorias que ainda não existem no banco do usuário são criadas
automaticamente durante a importação — diferente da análise por IA,
que restringe a categoria a uma lista fixa.

Linhas inválidas não interrompem a importação: o resultado retorna
quantas linhas foram inseridas com sucesso e uma lista de erros por
linha.
