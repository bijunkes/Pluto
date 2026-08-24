import json

import ollama

from src.config.categorias import CATEGORIAS

class LlamaService:

    def __init__(self):

        # Categorias disponíveis para classificar a compra
        self.categorias = CATEGORIAS

    def analisar_mensagem(self, mensagem):

        categorias_disponiveis = ", ".join(
            self.categorias
        )

        prompt = f"""
        Você é o sistema de análise de compras do Pluto.

        Analise a mensagem enviada pelo usuário.

        Mensagem:
        "{mensagem}"

        Identifique SOMENTE:

        - produto: objeto comprado
        - categoria: categoria geral do produto
        - valor: preço pago

        Categorias disponíveis:
        {categorias_disponiveis}

        Regras:
        1. Não invente informações.
        2. A categoria DEVE ser uma das categorias disponíveis.
        3. NÃO crie uma nova categoria.
        4. Escolha a categoria que melhor representa o produto.
        5. Se nenhuma categoria for adequada, use "Outros".
        6. O valor deve ser obtido da mensagem quando estiver presente.
        7. Se não conseguir identificar o produto, use "Não informado".
        8. Se não conseguir identificar o valor, use 0.
        9. O valor deve ser um número decimal.

        Retorne SOMENTE um JSON válido neste formato:

        {{
            "produto": "nome do produto",
            "categoria": "categoria",
            "valor": 0.0
        }}
        """

        response = ollama.chat(
            model="llama3.2",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        texto = response["message"]["content"]

        return json.loads(texto)
