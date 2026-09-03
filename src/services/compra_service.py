from src.services.ia_service import IAService
from src.database.database import Database


class CompraService:

    def __init__(self, usuario_id, ia_service=None):
        """
        Inicializa o serviço responsável pelo processamento
        das compras do usuário.
        """

        self.database = Database(usuario_id)

        self.ia = ia_service if ia_service else IAService()

    # =========================================================
    # COMPRA
    # =========================================================

    def processar_compra(self, mensagem, imagem_path=None):
        """
        Analisa uma compra utilizando o Gemini.
        """

        resultado = self.ia.analisar_mensagem(
            mensagem=mensagem, imagem_path=imagem_path
        )

        print("\nCompra identificada:")
        print(f"Produto: {resultado['produto']}")
        print(f"Categoria: {resultado['categoria']}")
        print(f"Valor: R$ {resultado['valor']:.2f}")

        return resultado

    def confirmar_compra(self, resultado, conta_id):
        """
        Salva uma compra utilizando a categoria
        identificada pela IA e a conta escolhida
        pelo usuário.
        """

        compra_id = self.database.salvar_compra(
            produto=resultado["produto"],
            categoria=resultado["categoria"],
            conta_id=conta_id,
            valor=resultado["valor"],
        )

        print("\nCompra salva com sucesso!")

        return compra_id

    def confirmar_compra_com_categoria(self, resultado, categoria, conta_id):
        """
        Salva uma compra utilizando uma categoria
        escolhida manualmente e uma conta escolhida
        pelo usuário.
        """

        return self.database.salvar_compra(
            produto=resultado["produto"],
            categoria=categoria,
            conta_id=conta_id,
            valor=resultado["valor"],
        )

    # =========================================================
    # CATEGORIAS
    # =========================================================

    def adicionar_categoria(self, nome):
        """
        Adiciona uma categoria personalizada
        para o usuário.
        """

        return self.database.adicionar_categoria(nome)

    def listar_categorias(self):
        return self.database.listar_categorias()

    def listar_nomes_categorias(self):
        return self.database.listar_nomes_categorias()

    def categoria_existe(self, nome):
        return self.database.categoria_existe(nome)

    # =========================================================
    # CONTAS
    # =========================================================

    def listar_contas(self):
        """
        Retorna as contas ativas do usuário.
        """

        return self.database.listar_contas()

    def listar_nomes_contas(self):
        """
        Retorna apenas os nomes das contas ativas.
        """

        return self.database.listar_nomes_contas()

    def buscar_conta(self, conta_id):
        """
        Busca uma conta pelo ID.
        """

        return self.database.buscar_conta(conta_id)

    def adicionar_conta(self, nome, tipo, saldo=0):
        """
        Adiciona uma nova conta para o usuário.
        """

        return self.database.adicionar_conta(nome=nome, tipo=tipo, saldo=saldo)

    # =========================================================
    # HISTÓRICO DE COMPRAS
    # =========================================================

    def listar_compras(self, data_inicio=None, data_fim=None):
        return self.database.listar_compras(data_inicio=data_inicio, data_fim=data_fim)

    def buscar_compra(self, compra_id):
        return self.database.buscar_compra(compra_id)

    def excluir_compra(self, compra_id):
        return self.database.excluir_compra(compra_id)

    # =========================================================
    # ESTATÍSTICAS
    # =========================================================

    def calcular_total(self):
        """
        Calcula o total gasto pelo usuário.
        """

        compras = self.database.listar_compras()

        return sum(compra[4] for compra in compras)
