from datetime import datetime
from zoneinfo import ZoneInfo

from src.database.database import Database
from src.services.insight_service import InsightService
from src.services.groq_service import GroqService


class SchedulerService:
    """Processa os insights automáticos de todos os usuários configurados."""

    FUSO = ZoneInfo("America/Sao_Paulo")

    def __init__(self, ia_service=None):
        # Mantido na assinatura para compatibilidade com TelegramBot.
        self.ia_service = ia_service
        self.groq_service = GroqService()

    @classmethod
    def agora(cls):
        return datetime.now(cls.FUSO).replace(tzinfo=None)

    async def processar_insights(self, callback_envio):
        agora = self.agora()
        resultados = []

        # A lista é obtida por uma conexão independente do usuário.
        # Database usa o telegram_id apenas nas operações por usuário.
        configs = self._listar_configuracoes()

        for config in configs:
            telegram_id = config["telegram_id"]
            try:
                database = Database(telegram_id)
                insight_service = InsightService(database)

                deve_enviar = insight_service.deve_gerar_insight(agora)

                print(
                    f"[SCHEDULER] Usuário {telegram_id} | "
                    f"Frequência: {config['frequencia']} | "
                    f"Horário: {config['horario']} | "
                    f"Último envio: {config['ultimo_envio']} | "
                    f"Agora: {agora} | "
                    f"Deve enviar: {deve_enviar}"
                )

                if not deve_enviar:
                    continue

                print(f"[SCHEDULER] Gerando insight para {telegram_id}...")

                periodo = "diario" if config["frequencia"] == "DIARIO" else "semanal"

                dados = insight_service.gerar_dados_insight(periodo)

                mensagem = self.groq_service.gerar_insight(dados)

                print(
                    f"[SCHEDULER] Insight gerado para {telegram_id}: "
                    f"{mensagem}"
                )

                if not mensagem:
                    print(f"[SCHEDULER] IA não retornou mensagem para {telegram_id}.")
                    continue

                print(
                    f"[SCHEDULER] Enviando mensagem para Telegram: "
                    f"{telegram_id}..."
                )

                await callback_envio(telegram_id, mensagem)

                print(
                    f"[SCHEDULER] Mensagem enviada para Telegram: "
                    f"{telegram_id}"
                )

                database.registrar_envio_insight()

                resultados.append(telegram_id)

            except Exception as erro:
                print(f"[SCHEDULER] Erro no usuário {telegram_id}: {erro}")

        return resultados

    def _listar_configuracoes(self):
        # Não existe Database global porque a classe é orientada ao usuário.
        # A consulta é feita diretamente usando DATABASE_URL.
        import os
        import psycopg

        with psycopg.connect(os.getenv("DATABASE_URL"), prepare_threshold=None) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT telegram_id, ativo, frequencia, horario, ultimo_envio
                    FROM configuracoes_insights
                    WHERE ativo = TRUE
                    AND frequencia != 'NENHUM'
                    """
                )
                rows = cursor.fetchall()

        return [
            {
                "telegram_id": row[0],
                "ativo": row[1],
                "frequencia": row[2],
                "horario": row[3],
                "ultimo_envio": row[4],
            }
            for row in rows
        ]
