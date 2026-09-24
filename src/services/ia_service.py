from src.services.gemini_service import GeminiService
from src.services.groq_service import GroqService
from src.services.exceptions import AnaliseIAError


class IAService:

    def __init__(self):
        self.gemini = GeminiService()
        self.groq = GroqService()

    def analisar_mensagem(self, mensagem, imagem_path=None):
        try:
            return self.gemini.analisar_mensagem(
                mensagem=mensagem, imagem_path=imagem_path
            )
        except AnaliseIAError as erro:
            print(f"[IA] Gemini falhou: {erro}")

        # =====================================================
        # FAILOVER → GROQ
        # =====================================================

        print("[IA] Ativando Groq como fallback...")

        # Groq nesse momento está configurado apenas para texto
        if imagem_path:

            raise AnaliseIAError(
                "O Gemini está indisponível no momento "
                "e o Groq não está configurado para "
                "análise de imagens."
            )

        try:

            resultado = self.groq.analisar_mensagem(mensagem=mensagem)

            print("[IA] Compra analisada com sucesso pelo Groq.")

            return resultado

        except AnaliseIAError as e:

            print(f"[IA] Groq também falhou: {e}")

            raise AnaliseIAError(
                "Não foi possível analisar a compra " "nem pelo Gemini nem pelo Groq."
            ) from e

    def gerar_insight(self, dados):
        """
        Gera um insight financeiro utilizando o Gemini
        e utiliza o Groq como fallback.
        """

        try:

            print("[IA] Gerando insight pelo Gemini...")

            return self.gemini.gerar_insight(dados)

        except AnaliseIAError as e:

            print(f"[IA] Gemini falhou ao gerar insight: {e}")

        # =====================================================
        # FAILOVER → GROQ
        # =====================================================

        print("[IA] Ativando Groq como fallback para insight...")

        try:

            resultado = self.groq.gerar_insight(dados)

            print("[IA] Insight gerado com sucesso pelo Groq.")

            return resultado

        except AnaliseIAError as e:

            print(f"[IA] Groq também falhou ao gerar insight: {e}")

            raise AnaliseIAError(
                "Não foi possível gerar o insight "
                "nem pelo Gemini nem pelo Groq."
            ) from e
