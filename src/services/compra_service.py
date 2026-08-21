from src.services.gemini_service import GeminiService
from src.database.database import Database

class CompraService:

    def __init__(self, gemini_service, database):
        self.gemini_service = gemini_service
        self.database = database

    def processar_compra(self, mensagem, imagem_path=None):

        resultado = self.gemini_service.analisar_compra(
            imagem_path=imagem_path,
            mensagem=mensagem
        )

        print("\nCompra identificada:")
        print(f"Produto: {resultado['produto']}")
        print(f"Categoria: {resultado['categoria']}")
        print(f"Valor: R$ {resultado['valor']:.2f}")

        return resultado

    def confirmar_compra(self, resultado):

        self.database.salvar_compra(
            produto=resultado["produto"],
            categoria=resultado["categoria"],
            valor=resultado["valor"]
        )

        print("\nCompra salva com sucesso!")
