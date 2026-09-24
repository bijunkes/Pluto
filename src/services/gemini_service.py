import os
import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from datetime import datetime
from zoneinfo import ZoneInfo

from src.config.categorias import CATEGORIAS
from src.services.exceptions import AnaliseIAError
from src.services.ia_utils import extrair_json, validar_resultado_compra


class GeminiService:

    # Garante que a chave de API existe antes de iniciar o cliente
    def __init__(self):
        load_dotenv()

        if "GEMINI_API_KEY" not in os.environ:
            raise AnaliseIAError(
                "A variável de ambiente GEMINI_API_KEY não foi configurada no arquivo .env"
            )

        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.categorias = CATEGORIAS

    def analisar_mensagem(self, mensagem, imagem_path=None):
        """
        Analisa a mensagem do usuário (e imagem opcional) utilizando a API do Gemini
        para extrair o produto, categoria e valor da compra.
        """
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
    * data_compra: data em que a compra aconteceu, se informada pelo usuário
    * hora_compra: horário em que a compra aconteceu, se informado pelo usuário

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
    Data e hora atual:
    {datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%Y-%m-%d %H:%M")}

    Regras para data e hora:

    10. Se o usuário informar uma data, converta para o formato YYYY-MM-DD.
    11. Se o usuário usar expressões como "hoje", "ontem" ou "anteontem",
        interprete com base na data atual fornecida acima.
    12. Se o usuário informar uma hora, converta para o formato HH:MM.
    13. Expressões como "às 18h", "18 horas", "18:30" devem ser convertidas
        para HH:MM.
    14. Se o usuário NÃO informar a data, retorne null em data_compra.
    15. Se o usuário NÃO informar a hora, retorne null em hora_compra.
    16. NÃO invente data ou hora.
    """

        contents = []

        if imagem_path:
            try:
                with open(imagem_path, "rb") as f:
                    imagem = f.read()

                contents.append(
                    types.Part.from_bytes(data=imagem, mime_type="image/jpeg")
                )

            except Exception as e:
                raise AnaliseIAError(f"Erro ao ler a imagem enviada: {str(e)}")

        contents.append(prompt)

        try:

            max_tentativas = 3

            for tentativa in range(max_tentativas):

                try:

                    response = self.client.models.generate_content(
                        model="gemini-3.6-flash",
                        contents=contents,
                        config=types.GenerateContentConfig(
                            response_mime_type="application/json",
                            response_schema=types.Schema(
                                type="OBJECT",
                                properties={
                                    "produto": types.Schema(type="STRING"),
                                    "categoria": types.Schema(type="STRING"),
                                    "valor": types.Schema(type="NUMBER"),
                                    "data_compra": types.Schema(
                                        type="STRING", nullable=True
                                    ),
                                    "hora_compra": types.Schema(
                                        type="STRING", nullable=True
                                    ),
                                },
                                required=[
                                    "produto",
                                    "categoria",
                                    "valor",
                                    "data_compra",
                                    "hora_compra",
                                ],
                            ),
                        ),
                    )

                    break

                except Exception as e:

                    erro = str(e)

                    if "503" in erro or "UNAVAILABLE" in erro or "high demand" in erro:

                        if tentativa < max_tentativas - 1:

                            espera = 2**tentativa

                            print(
                                f"Gemini indisponível. "
                                f"Tentativa {tentativa + 1}/{max_tentativas}. "
                                f"Aguardando {espera}s..."
                            )

                            time.sleep(espera)

                            continue

                    raise

            resultado = extrair_json(response.text)

            validar_resultado_compra(resultado, self.categorias)

            return resultado

        except Exception as e:

            raise AnaliseIAError(
                "Não foi possível se comunicar com o Gemini. " f"Detalhes: {str(e)}"
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

            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
            )

            return response.text.strip()

        except Exception as e:

            raise AnaliseIAError(
                "Não foi possível gerar o insight pelo Gemini. " f"Detalhes: {str(e)}"
            ) from e
