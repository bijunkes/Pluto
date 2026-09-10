from src.database.database import Database
from src.services.insight_service import InsightService
from src.services.ia_service import IAService


class SchedulerService:

    def __init__(self, ia_service):
        self.database = Database(None)
        self.ia_service = ia_service

    def verificar_insights(self):
        """
        Verifica quais usuários precisam receber
        um insight automático.
        """

        configuracoes = (
            self.database.listar_configuracoes_insights_ativas()
        )

        usuarios_para_processar = []

        for configuracao in configuracoes:
            telegram_id = configuracao["telegram_id"]

            database_usuario = Database(telegram_id)
            insight_service = InsightService(database_usuario)

            if insight_service.deve_gerar_insight():
                usuarios_para_processar.append(
                    {
                        "telegram_id": telegram_id,
                        "frequencia": configuracao["frequencia"],
                    }
                )

        return usuarios_para_processar

    async def processar_insights(self, enviar_mensagem):
        """
        Gera e envia os insights dos usuários que estão
        no momento correto para receber um insight.

        O envio é feito através da função recebida em
        enviar_mensagem.

        O último envio só é registrado depois que
        a mensagem for enviada com sucesso.
        """

        usuarios = self.verificar_insights()

        resultados = []

        for usuario in usuarios:

            telegram_id = usuario["telegram_id"]
            frequencia = usuario["frequencia"]

            try:

                database_usuario = Database(telegram_id)

                insight_service = InsightService(
                    database_usuario
                )

                dados = insight_service.gerar_dados_insight(
                    frequencia.lower()
                )

                insight = self.ia_service.gerar_insight(
                    dados
                )

                # Envia a mensagem pelo Telegram
                await enviar_mensagem(
                    telegram_id,
                    insight
                )

                # Só registra o envio depois que
                # o Telegram confirmar o envio.
                database_usuario.registrar_envio_insight()

                resultados.append(
                    {
                        "telegram_id": telegram_id,
                        "frequencia": frequencia,
                        "dados": dados,
                        "insight": insight,
                        "enviado": True,
                    }
                )

                print(
                    f"[SCHEDULER] Insight enviado para "
                    f"{telegram_id}"
                )

            except Exception as erro:

                print(
                    f"[SCHEDULER] Erro ao processar "
                    f"usuário {telegram_id}: {erro}"
                )

                resultados.append(
                    {
                        "telegram_id": telegram_id,
                        "frequencia": frequencia,
                        "enviado": False,
                        "erro": str(erro),
                    }
                )

        return resultados
