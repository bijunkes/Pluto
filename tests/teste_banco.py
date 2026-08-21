from src.database.database import salvar_compra

salvar_compra(
    produto="Camisa da Seleção Brasileira",
    categoria="Roupas",
    valor=129.90
)

print("Compra salva com sucesso!")