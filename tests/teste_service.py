from src.services.gemini_service import GeminiService
from src.services.compra_service import CompraService
from src.database.database import Database


database = Database()
database.criar_tabelas()
database.inserir_categorias()

gemini = GeminiService()

compra_service = CompraService(
    gemini_service=gemini,
    database=database
)

resultado = compra_service.processar_compra(
    mensagem="Comprei uma camisa por R$ 129,90"
)

compra_service.confirmar_compra(resultado)

print("\nCompras:")
print(database.listar_compras())