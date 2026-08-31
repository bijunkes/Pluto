from src.services.gemini_service import GeminiService
from src.database.database import Database


class CompraService:

    def __init__(
        self,
        usuario_id,
        gemini_service=None
    ):
        """
        Inicializa o serviço responsável pelo processamento
        das compras do usuário.

        O usuario_id corresponde ao ID do usuário no Telegram.
        """

        # Banco PostgreSQL compartilhado.
        # O Database utiliza o telegram_id para isolar
        # os dados personalizados de cada usuário.
        self.database = Database(usuario_id)

        # Serviço responsável pela análise das compras
        # utilizando inteligência artificial.
        self.gemini = (
            gemini_service
            if gemini_service
            else GeminiService()
        )

    def processar_compra(
        self,
        mensagem,
        imagem_path=None
    ):
        """
        Analisa uma compra utilizando o Gemini.
        """

        resultado = self.gemini.analisar_mensagem(
            mensagem=mensagem,
            imagem_path=imagem_path
        )

        print("\nCompra identificada:")
        print(f"Produto: {resultado['produto']}")
        print(f"Categoria: {resultado['categoria']}")
        print(f"Valor: R$ {resultado['valor']:.2f}")

        return resultado

    def confirmar_compra(self, resultado):
        """
        Salva uma compra utilizando a categoria
        identificada pela IA.
        """

        compra_id = self.database.salvar_compra(
            produto=resultado["produto"],
            categoria=resultado["categoria"],
            valor=resultado["valor"]
        )

        print("\nCompra salva com sucesso!")

        return compra_id

    def adicionar_categoria(self, nome):
        """
        Adiciona uma categoria personalizada
        para o usuário.
        """

        return self.database.adicionar_categoria(nome)

    def confirmar_compra_com_categoria(
        self,
        resultado,
        categoria
    ):
        """
        Salva uma compra utilizando uma categoria
        escolhida manualmente pelo usuário.
        """

        return self.database.salvar_compra(
            produto=resultado["produto"],
            categoria=categoria,
            valor=resultado["valor"]
        )

    def listar_categorias(self):
        """
        Retorna as categorias padrão e as categorias
        personalizadas disponíveis para o usuário.
        """

        return self.database.listar_categorias()

    def listar_nomes_categorias(self):
        """
        Retorna apenas os nomes das categorias
        disponíveis para o usuário.
        """

        return self.database.listar_nomes_categorias()

    def listar_compras(
        self,
        data_inicio=None,
        data_fim=None
    ):
        """
        Retorna as compras do usuário.

        Opcionalmente permite filtrar por período.
        """

        return self.database.listar_compras(
            data_inicio=data_inicio,
            data_fim=data_fim
        )

    def buscar_compra(self, compra_id):
        """
        Busca uma compra específica do usuário.
        """

        return self.database.buscar_compra(
            compra_id
        )

    def excluir_compra(self, compra_id):
        """
        Exclui uma compra pertencente ao usuário.
        """

        return self.database.excluir_compra(
            compra_id
        )

    def categoria_existe(self, nome):
        """
        Verifica se uma categoria está disponível
        para o usuário.
        """

        return self.database.categoria_existe(
            nome
        )

    def calcular_total(self):
        """
        Calcula o total gasto pelo usuário.
        """

        compras = self.database.listar_compras()

        return sum(
            compra[3]
            for compra in compras
        )