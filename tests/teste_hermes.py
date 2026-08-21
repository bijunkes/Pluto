from src.hermes import processar_compra, confirmar_compra


resultado = processar_compra(
    mensagem="Comprei uma camisa por R$ 129,90",
    imagem_path="produto.jpg"
)

resposta = input("\nDeseja registrar essa compra? (s/n): ")

if resposta.lower() == "s":
    confirmar_compra(resultado)
else:
    print("\nCompra não registrada.")