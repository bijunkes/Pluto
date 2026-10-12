# Dependências iniciais

Fonte: `requirements.txt` e `requirements-dev.txt`, versões mínimas declaradas, não versões efetivamente instaladas.

| Componente | Dependência declarada |
| --- | --- |
| Bot Telegram | `python-telegram-bot>=22.8` |
| API | `fastapi>=0.141.1`, `uvicorn[standard]>=0.52.4`, `pydantic>=2.13.4` |
| Banco de dados | `psycopg[binary]>=3.3.4` |
| IA | `google-genai>=2.19.0`, `groq>=1.7.0` |
| Dados e configuração | `pandas>=3.0.5`, `python-dotenv>=1.2.3` |
| Testes | `pytest>=9.1.1` |

Gerenciador: pip, com arquivos `requirements*.txt`.
