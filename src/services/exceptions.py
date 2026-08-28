class AnaliseIAError(Exception):
    """
    Erro lançado quando um serviço de IA (Gemini ou Llama)
    não consegue analisar a compra corretamente.

    Isso cobre tanto falhas de comunicação com o modelo
    quanto respostas que não vêm em um JSON válido ou que
    não têm os campos esperados (produto, categoria, valor).
    """
    pass
