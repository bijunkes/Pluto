from src.database.database import Database
from src.services.insight_service import InsightService
from src.services.ia_service import IAService


USUARIO_ID = 7212357907


database = Database(USUARIO_ID)
insight_service = InsightService(database)
ia_service = IAService()


print("\n========== PREPARANDO DADOS ==========\n")

analise = insight_service.gerar_analise_semanal()

dados_ia = insight_service.preparar_dados_para_ia(
    analise
)

print(dados_ia)


print("\n========== GERANDO INSIGHT ==========\n")

insight = ia_service.gerar_insight(
    dados_ia
)

print(insight)
