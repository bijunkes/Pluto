import time

from src.services.gemini_service import GeminiService
from src.services.groq_service import GroqService
from src.services.exceptions import AnaliseIAError


class IAService:

    def __init__(self):
        self.gemini = GeminiService()
        self.groq = GroqService()

    def analisar_mensagem(self, mensagem, imagem_path=None):

        ultimo_erro = None

        # =====================================================
        # GEMINI
        # =====================================================

        for tentativa in range(3):

            try:

                print(f"[IA] Gemini - tentativa " f"{tentativa + 1}/3")

                return self.gemini.analisar_mensagem(
                    mensagem=mensagem, imagem_path=imagem_path
                )

            except AnaliseIAError as e:

                ultimo_erro = e
                erro = str(e)

                print(f"[IA] Gemini falhou: {erro}")

                # -------------------------------------------------
                # 429 = COTA EXCEDIDA
                # Não adianta tentar novamente
                # -------------------------------------------------

                if (
                    "429" in erro
                    or "RESOURCE_EXHAUSTED" in erro
                    or "quota" in erro.lower()
                ):
                    print(
                        "[IA] Cota do Gemini excedida. " "Ativando failover para Groq."
                    )
                    break

                # -------------------------------------------------
                # 400 = CHAVE INVÁLIDA
                # Não adianta tentar novamente
                # -------------------------------------------------

                if (
                    "400" in erro
                    or "API_KEY_INVALID" in erro
                    or "API key not valid" in erro
                ):
                    print(
                        "[IA] Chave do Gemini inválida. " "Ativando failover para Groq."
                    )
                    break

                # -------------------------------------------------
                # 503 = ERRO TEMPORÁRIO
                # Pode tentar novamente
                # -------------------------------------------------

                if "503" in erro or "UNAVAILABLE" in erro or "high demand" in erro:

                    if tentativa < 2:

                        espera = 2**tentativa

                        print(
                            f"[IA] Gemini indisponível. "
                            f"Tentativa {tentativa + 1}/3. "
                            f"Aguardando {espera}s..."
                        )

                        time.sleep(espera)

                        continue

                # Outro erro → vai direto para o fallback
                break

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