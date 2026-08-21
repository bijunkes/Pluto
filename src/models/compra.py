class Compra:

    def __init__(self, produto, categoria, valor):
        self.produto = produto
        self.categoria = categoria
        self.valor = valor

    def __str__(self):
        return (
            f"Produto: {self.produto}\n"
            f"Categoria: {self.categoria}\n"
            f"Valor: R$ {self.valor:.2f}"
        )