from datetime import datetime

from src.services.scheduler_service import SchedulerService


USUARIO_ID = 7212357907

scheduler = SchedulerService()


print("\n========== TESTE DO PROCESSAMENTO DE INSIGHT ==========")

# Simula que o usuário ainda não recebeu
# o insight de hoje.
with scheduler.database.conectar() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE configuracoes_insights
            SET
                frequencia = 'DIARIO',
                ativo = TRUE,
                horario = '09:00',
                ultimo_envio = %s
            WHERE telegram_id = %s
            """,
            (
                datetime(2026, 9, 7, 9, 0),
                USUARIO_ID,
            ),
        )


print("\nExecutando processamento...")

resultados = scheduler.processar_insights()


print("\nResultados:")

for resultado in resultados:
    print("\nTelegram ID:")
    print(resultado["telegram_id"])

    print("\nFrequência:")
    print(resultado["frequencia"])

    print("\nDados enviados para IA:")
    print(resultado["dados"])

    print("\nInsight gerado:")
    print(resultado["insight"])

def enviar_mensagem_fake(telegram_id, mensagem):
    print("\n========== ENVIO SIMULADO ==========")
    print(f"Telegram ID: {telegram_id}")
    print(f"Mensagem: {mensagem}")
    print("====================================\n")


scheduler = SchedulerService()

resultados = scheduler.processar_insights(
    enviar_mensagem=enviar_mensagem_fake
)

print("\n========== RESULTADOS ==========")

for resultado in resultados:
    print(resultado)