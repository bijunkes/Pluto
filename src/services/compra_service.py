from src.services.gemini_service import GeminiService
from src.services.llama_service import LlamaService
from src.database.database import Database

class CompraService:

    def __init__(
        self,
        usuario_id,
        gemini_service=None,
        llama_service=None
    ):
        """
        Inicializa o serviço responsável pelo processamento das compras.

        Cada usuário possui seu próprio banco de dados.
        O Gemini analisa imagens e o Llama interpreta
        mensagens de texto.
        """

        # Banco exclusivo do usuário
        self.database = Database(usuario_id)

        # Serviço responsável pela análise de imagens
        self.gemini = (
            gemini_service
            if gemini_service
            else GeminiService()
        )

        # Serviço responsável pela interpretação de mensagens
        self.llama = (
            llama_service
            if llama_service
            else LlamaService()
        )

    def processar_compra(
        self,
        mensagem,
        imagem_path=None
    ):
        """
        Processa uma compra utilizando o serviço adequado.

        - Com imagem → Gemini
        - Somente texto → Llama
        """

        if imagem_path:

            resultado = self.gemini.analisar_compra(
                imagem_path=imagem_path,
                mensagem=mensagem
            )

        else:

            resultado = self.llama.analisar_mensagem(
                mensagem=mensagem
            )

        print("\nCompra identificada:")
        print(f"Produto: {resultado['produto']}")
        print(f"Categoria: {resultado['categoria']}")
        print(f"Valor: R$ {resultado['valor']:.2f}")

        return resultado

    def confirmar_compra(self, resultado):
        """
        Salva uma compra utilizando a categoria
        identificada automaticamente pela IA.
        """

        self.database.salvar_compra(
            produto=resultado["produto"],
            categoria=resultado["categoria"],
            valor=resultado["valor"]
        )

        print("\nCompra salva com sucesso!")

    def adicionar_categoria(self, nome):
        """
        Adiciona uma nova categoria ao banco do usuário.
        """

        self.database.adicionar_categoria(nome)

    def confirmar_compra_com_categoria(
        self,
        resultado,
        categoria
    ):
        """
        Salva uma compra utilizando uma categoria
        escolhida manualmente pelo usuário.
        """

        self.database.salvar_compra(
            produto=resultado["produto"],
            categoria=categoria,
            valor=resultado["valor"]
        )