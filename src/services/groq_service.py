import os
import json

from dotenv import load_dotenv
from groq import Groq

from src.config.categorias import CATEGORIAS
from src.services.exceptions import AnaliseIAError
from src.services.ia_utils import extrair_json, validar_resultado_compra


class GroqService:

    def __init__(self):

        load_dotenv()

        if "GROQ_API_KEY" not in os.environ:

            raise AnaliseIAError(
                "A variável de ambiente GROQ_API_KEY "
                "não foi configurada no arquivo .env"
            )

        self.client = Groq(api_key=os.environ["GROQ_API_KEY"])

        self.categorias = CATEGORIAS

    def analisar_mensagem(self, mensagem):

        categorias_disponiveis = ", ".join(self.categorias)

        prompt = f"""
Você é o sistema de análise de compras do Pluto.

Analise as informações fornecidas pelo usuário.

Mensagem do usuário:
"{mensagem}"

Identifique SOMENTE:

* produto: objeto comprado
* categoria: categoria geral do produto
* valor: preço pago

Categorias disponíveis:
{categorias_disponiveis}

Regras:

1. Não invente informações.
2. A categoria DEVE ser escolhida entre as categorias disponíveis.
3. NÃO crie uma nova categoria.
4. Escolha a categoria que melhor representa o produto.
5. Se nenhuma categoria for adequada, use "Outros".
6. O valor deve ser obtido da mensagem quando estiver presente.
7. Se não conseguir identificar produto, use "Não informado".
8. Se não conseguir identificar o valor, use 0.
9. O valor deve ser um número decimal.

Retorne SOMENTE um JSON válido neste formato:

{{
    "produto": "nome do produto",
    "categoria": "categoria",
    "valor": 0.0
}}
"""

        try:

            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                response_format={"type": "json_object"},
            )

            texto = response.choices[0].message.content

            resultado = extrair_json(texto)

            return validar_resultado_compra(resultado, self.categorias)

        except Exception as e:

            raise AnaliseIAError(
                "Não foi possível se comunicar " f"com o Groq. Detalhes: {str(e)}"
            ) from e

    def gerar_insight(self, dados):
        """
        Gera um insight financeiro a partir dos dados
        previamente calculados pelo InsightService.
        """

        prompt = f"""
Você é o assistente financeiro do Pluto.

Sua função é transformar dados financeiros já calculados
pelo sistema em um insight curto, útil e amigável.

Dados da análise:

{json.dumps(dados, ensure_ascii=False, indent=2)}

Regras:

1. Use SOMENTE os dados fornecidos.
2. Não invente valores, categorias ou informações.
3. Não faça cálculos diferentes dos dados fornecidos.
4. Não dê diagnósticos financeiros.
5. Não seja julgador ou alarmista.
6. Seja objetivo e natural.
7. Destaque apenas os padrões mais relevantes.
8. Gere no máximo 2 insights.
9. Se não houver um padrão relevante, informe isso de forma simples.
10. Os valores devem ser apresentados em reais brasileiros.
11. Não mencione que você é uma IA.
12. Não use Markdown complexo.
13. O resultado deve ser apenas o texto que será enviado ao usuário.

Escreva o insight em português do Brasil.
"""

        try:

            response = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.3,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:

            raise AnaliseIAError(
                "Não foi possível gerar o insight pelo Groq. "
                f"Detalhes: {str(e)}"
            ) from e