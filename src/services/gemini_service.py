import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.config.categorias import CATEGORIAS
from src.services.exceptions import AnaliseIAError
from src.services.ia_utils import extrair_json, validar_resultado_compra

class GeminiService:

    # Garante que a chave de API existe antes de iniciar o cliente
    def __init__(self):
        load_dotenv()

        if "GEMINI_API_KEY" not in os.environ:
            raise AnaliseIAError("A variável de ambiente GEMINI_API_KEY não foi configurada no arquivo .env")

        self.client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )
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
    """

        contents = []

        ### Se houver uma imagem (ex: foto de recibo), adiciona na chamada

        if imagem_path:
            try:
                with open(imagem_path, "rb") as f:
                    imagem = f.read()
                contents.append(
                    types.Part.from_bytes(
                        data=imagem,
                        mime_type="image/jpeg"
                    )
                )
            except Exception as e:
                raise AnaliseIAError(f"Erro ao ler a imagem enviada: {str(e)}")

        contents.append(prompt)

        try:

            # Utilizando o modelo flash recomendado para tarefas de texto/multimodal estruturado

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
                            "valor": types.Schema(type="NUMBER")
                        },
                        required=["produto", "categoria", "valor"]
                    )
                )
            )

        except Exception as e:
            raise AnaliseIAError(
                f"Não foi possível se comunicar com o Gemini. Detalhes: {str(e)}"
            ) from e

        ### Processa o texto puro retornado e valida com as funções utilitárias do projeto

        resultado = extrair_json(response.text)
        return validar_resultado_compra(resultado, self.categorias)