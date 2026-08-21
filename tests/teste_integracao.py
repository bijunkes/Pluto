from src.gemini import analisar_compra
from src.database.database import salvar_compra

resultado = analisar_compra(
    imagem_path="produto.jpg",
    mensagem="Paguei R$ 129,90 por essa camisa."
)

print("Resultado da IA:")
print(resultado)

salvar_compra(
    produto=resultado["produto"],
    categoria=resultado["categoria"],
    valor=resultado["valor"]
)

print("Compra salva no banco!")