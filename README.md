<p align="center">
  <img src="./logo.png" alt="Logo do Pluto" width="180">
</p>

<h1 align="center">PLUTO</h1>

<p align="center">
  <strong>Assistente Financeiro Inteligente</strong>
</p>

<p align="center">
  Converse com o Pluto pelo Telegram e transforme sua rotina financeira em uma conversa.
</p>

<p align="center">
  <a href="https://plutoassistente.vercel.app">
    🌐 Landing Page
  </a>
  &nbsp;&nbsp;•&nbsp;&nbsp;
  <a href="https://t.me/PlutoTrackerBot">
    💬 Conversar com o Pluto
  </a>
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge\&logo=python\&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge\&logo=fastapi\&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge\&logo=postgresql\&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge\&logo=telegram\&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?style=for-the-badge\&logo=google\&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-F55036?style=for-the-badge)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge\&logo=javascript\&logoColor=black)

</p>

O **Pluto** é um assistente financeiro inteligente desenvolvido para tornar o controle das finanças pessoais mais simples e acessível.

A principal proposta do projeto é permitir que o usuário **converse naturalmente com o Pluto pelo Telegram** para registrar e consultar suas informações financeiras.

Em vez de preencher formulários ou navegar por diversas telas, o usuário pode simplesmente enviar uma mensagem como:

```text
"Comprei um café por R$ 8,50"
```

O Pluto utiliza **Inteligência Artificial** para interpretar a mensagem, identificar as informações relevantes e transformar a conversa em um registro financeiro estruturado.

Além do registro de compras, o Pluto permite gerenciar contas e categorias, consultar o histórico financeiro e visualizar os dados por meio de um dashboard.

---

## 💬 Converse com o Pluto

O Pluto foi pensado para que o controle financeiro aconteça de forma natural, através de uma conversa.

O usuário pode escrever como normalmente falaria com uma pessoa:

```text
"gastei 42 reais no mercado"
```

```text
"comprei um tênis por 250 reais"
```

```text
"paguei 30 reais de gasolina"
```

O Pluto interpreta a mensagem e apresenta os dados identificados antes de realizar o registro.

### Exemplo

```text
👤 Você:

Comprei uma pizza por 65 reais


🐶 Pluto:

Entendi! Encontrei estes dados:

🍕 Produto: Pizza
💰 Valor: R$ 65,00
🏷️ Categoria: Alimentação

Deseja registrar essa compra?

[✅ Confirmar] [✏️ Corrigir]
```

A proposta é transformar o **controle financeiro em uma conversa**, tornando o processo mais rápido e intuitivo para o dia a dia.

---

# 🐕 Funcionalidades

## 💬 Registro de compras por conversa

O usuário pode registrar uma compra simplesmente conversando com o Pluto.

A Inteligência Artificial identifica informações como:

* Produto
* Valor
* Categoria

Depois da interpretação, o Pluto solicita a confirmação do usuário antes de salvar o registro.

---

## 📷 Registro por imagem

Também é possível enviar uma **foto relacionada à compra**.

A IA analisa a imagem e utiliza as informações disponíveis para auxiliar na identificação dos dados da compra.

O usuário ainda pode corrigir as informações antes da confirmação.

---

## 🏦 Gerenciamento de contas

O Pluto permite cadastrar diferentes tipos de contas financeiras:

* Conta corrente
* Carteira
* Poupança
* Investimento

As compras podem ser associadas às contas cadastradas pelo usuário.

---

## 🏷️ Categorias

O sistema possui categorias padrão para facilitar a organização das compras.

Além disso, o usuário pode criar **categorias personalizadas** de acordo com sua própria rotina financeira.

---

## 📋 Histórico de compras

O usuário pode consultar suas compras registradas diretamente pelo Telegram.

```text
/compras
```

O Pluto apresenta os registros armazenados para facilitar o acompanhamento dos gastos.

---

## 📊 Dashboard

O Pluto possui um dashboard para apresentar as informações financeiras de forma visual e organizada.

O acesso ao dashboard pode ser realizado através do Telegram:

```text
/dashboard
```

O usuário recebe um link de acesso para visualizar seus dados.

---

## 🔐 Acesso ao dashboard

O Pluto não exige um cadastro tradicional.

O usuário é identificado pelo seu **Telegram ID**.

Quando deseja acessar o dashboard, o Pluto gera um **link de acesso temporário**, com validade limitada, enviado diretamente pela conversa no Telegram.

---

# 📱 Comandos do Telegram

Embora a principal interação aconteça através de conversa natural, o Pluto também disponibiliza comandos para facilitar a navegação.

| Comando      | Descrição                    |
| ------------ | ---------------------------- |
| `/start`     | Inicia o Pluto               |
| `/menu`      | Abre o menu principal        |
| `/help`      | Mostra a ajuda               |
| `/compras`   | Lista as compras registradas |
| `/contas`    | Lista as contas cadastradas  |
| `/dashboard` | Acessa o dashboard           |

O menu principal também disponibiliza:

* 💰 Registrar compra
* 🏦 Minhas contas
* 📋 Minhas compras
* 📊 Dashboard
* 🏷️ Criar categoria
* ❓ Ajuda

---

# 🤖 Inteligência Artificial

A Inteligência Artificial é uma das principais partes do Pluto.

Ela é responsável por transformar mensagens e imagens enviadas pelo usuário em informações estruturadas que podem ser utilizadas pelo sistema.

Por exemplo:

```text
Entrada:

"Comprei um hambúrguer por 32 reais"

↓

IA

↓

Produto: Hambúrguer
Valor: R$ 32,00
Categoria: Alimentação
```

O usuário recebe os dados interpretados e pode confirmar ou corrigir as informações antes que elas sejam armazenadas.

---

# 🔄 Fallback de IA

O projeto possui uma estratégia de fallback entre provedores de Inteligência Artificial.

O **Gemini** é utilizado como provedor principal e, em caso de falha ou indisponibilidade, o **Groq** pode ser utilizado como alternativa.

```text
                 ┌───────────────┐
                 │ Mensagem/Fot. │
                 └───────┬───────┘
                         │
                         ▼
                 ┌───────────────┐
                 │    Gemini     │
                 └───────┬───────┘
                         │
                    Sucesso?
                    /       \
                  SIM        NÃO
                   │          │
                   ▼          ▼
               Resultado     Groq
                              │
                              ▼
                           Resultado
```

Essa abordagem ajuda a manter o processamento disponível mesmo quando o provedor principal apresenta instabilidade.

---

# 🧠 Fluxo do sistema

O fluxo principal do Pluto acontece da seguinte maneira:

```text
                  ┌─────────────────┐
                  │     Usuário     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    Telegram     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Pluto Bot     │
                  │ Python / PTB    │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │  Serviço de IA  │
                  │ Gemini / Groq   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │ Dados extraídos │
                  │ produto/valor/  │
                  │ categoria       │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   Confirmação   │
                  │    do usuário   │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │   PostgreSQL    │
                  │    Supabase     │
                  └────────┬────────┘
                           │
                           ▼
                  ┌─────────────────┐
                  │    Dashboard    │
                  └─────────────────┘
```

---

# 🛠️ Tecnologias utilizadas

## Backend

* **Python**
* **FastAPI**
* **Uvicorn**
* **python-telegram-bot**
* **Pandas**

## Banco de dados

* **PostgreSQL**
* **Supabase**
* **psycopg**

## Inteligência Artificial

* **Google Gemini**
* **Google GenAI**
* **Groq**

## Frontend

* **HTML5**
* **CSS3**
* **JavaScript**

## Integrações

* **Telegram Bot API**
* **ngrok**
* **CORS**

## Deploy

* **Vercel** — Landing Page

---

# 🗄️ Banco de dados

O Pluto utiliza **PostgreSQL**, hospedado através do **Supabase**.

O banco é responsável pelo armazenamento das principais informações da aplicação, incluindo:

* Usuários
* Contas
* Compras
* Categorias

A identificação do usuário é realizada através do seu:

```text
telegram_id
```

Dessa forma, não é necessário criar um cadastro tradicional com usuário e senha para utilizar o bot.

---

# 🏗️ Arquitetura

O projeto foi desenvolvido separando as principais responsabilidades da aplicação.

De forma simplificada:

```text
Telegram
   │
   ▼
Handlers
   │
   ▼
Services
   │
   ├── IA Service
   ├── Compra Service
   ├── Conta Service
   └── Categoria Service
   │
   ▼
Database
   │
   ▼
PostgreSQL / Supabase
```

Essa organização facilita a manutenção e evolução do projeto.

---

# 📂 Estrutura do projeto

A estrutura pode variar conforme a versão atual do projeto, mas segue uma organização semelhante a:

```text
Projeto-Final-Entra21/
│
├── backend/
│   ├── ...
│   └── ...
│
├── frontend/
│   ├── ...
│   └── ...
│
├── LP/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   └── assets/
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

# 🌐 Landing Page

O Pluto também possui uma **Landing Page** criada para apresentar o projeto, suas funcionalidades e sua proposta.

A LP foi desenvolvida utilizando:

* HTML5
* CSS3
* JavaScript

E está hospedada utilizando o **Vercel**.

🔗 **Acesse a Landing Page:**

https://plutoassistente.vercel.app


---

# 👥 Equipe

Projeto desenvolvido durante o **Entra21 — Inteligência Artificial**.

### Integrantes

* **Felipe** — Apresentação e desenvolvimento
* **Bianca** — AI & Desenvolvimento Full Stack
* **Pavesi** — Desenvolvimento
* **Luan** — Desenvolvimento
* **Victoria** — Desenvolvimento

---

# 📚 Contexto acadêmico

O Pluto foi desenvolvido como **projeto final do curso de Inteligência Artificial do Entra21**.

Durante o desenvolvimento, foram aplicados conhecimentos de:

* Inteligência Artificial
* Desenvolvimento de APIs
* Desenvolvimento de bots
* Bancos de dados relacionais
* Desenvolvimento web
* Integração com APIs externas
* Arquitetura de software
* Experiência do usuário
* Git e GitHub

O projeto também envolveu a integração de diferentes tecnologias para criar uma solução completa, desde a interação do usuário no Telegram até o armazenamento e visualização dos dados.

---

# 📄 Licença

Este projeto foi desenvolvido para fins educacionais durante o programa **Entra21 — Inteligência Artificial**.

---

<p align="center">
  <img src="./logo.png" alt="Logo do Pluto" width="60">
  <br>
  <strong>Pluto</strong>
  <br>
  <em>Converse. Organize. Entenda suas finanças.</em>
</p>