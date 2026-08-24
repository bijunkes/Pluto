import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.config.categorias import CATEGORIAS


class GeminiService:

    def __init__(self):

        load_dotenv()

        self.client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

        self.categorias = CATEGORIAS

    def analisar_compra(
        self,
        imagem_path=None,
        mensagem=""
    ):

        categorias_disponiveis = ", ".join(
            self.categorias
        )

        prompt = f"""
        Você é o sistema de análise de compras do Pluto.

        Analise as informações fornecidas pelo usuário.

        Mensagem do usuário:
        "{mensagem}"

        Identifique SOMENTE:

        - produto: objeto comprado
        - categoria: categoria geral do produto
        - valor: preço pago

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

        if imagem_path:

            with open(imagem_path, "rb") as f:
                imagem = f.read()

            contents.append(
                types.Part.from_bytes(
                    data=imagem,
                    mime_type="image/jpeg"
                )
            )

        contents.append(prompt)

        response = self.client.models.generate_content(
            model="gemini-3.6-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=types.Schema(
                    type="OBJECT",
                    properties={
                        "produto": types.Schema(
                            type="STRING"
                        ),
                        "categoria": types.Schema(
                            type="STRING"
                        ),
                        "valor": types.Schema(
                            type="NUMBER"
                        )
                    },
                    required=[
                        "produto",
                        "categoria",
                        "valor"
                    ]
                )
            )
        )

        return json.loads(response.text)