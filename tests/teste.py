from src.gemini import analisar_compra


resultado = analisar_compra(
    "produto.jpg",
    "Paguei R$ 129,90 por essa camisa."
)

print(resultado)