from src.services.gemini_service import GeminiService
from src.database.database import Database

class CompraService:

    def __init__(
    self,
    usuario_id,
    gemini_service=None
    ):
        """
        Inicializa o serviço responsável pelo processamento das compras.
        Cada usuário possui seu próprio banco de dados.
        O Gemini analisa tanto mensagens de texto quanto imagens.
        """

        ### Banco exclusivo do usuário

        self.database = Database(usuario_id)

        # Serviço do Gemini unificado para texto e imagem

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
        Processa uma compra utilizando o Gemini. 

        O Gemini analisa o texto direto ou combina com a imagem se houver.
        """
        # Agora o Gemini Service gerencia de forma inteligente se há imagem ou não

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