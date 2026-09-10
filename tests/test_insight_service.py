from src.database.database import Database
from src.services.insight_service import InsightService
from datetime import datetime, timedelta


USUARIO_ID = 7212357907

database = Database(USUARIO_ID)
insight_service = InsightService(database)


print("\n========== ANÁLISE SEMANAL ==========\n")

analise = insight_service.gerar_analise_semanal()


print(f"Período: {analise['periodo']}")

print(
    f"\nTotal atual: "
    f"R$ {analise['atual']['total']:.2f}"
)

print(
    f"Total anterior: "
    f"R$ {analise['anterior']['total']:.2f}"
)


variacao = analise["variacao_total"]

if variacao is None:
    print("Variação total: não é possível calcular")
else:
    print(
        f"Variação total: "
        f"{variacao:.2f}%"
    )


print("\nVariações por categoria:")

for categoria in analise["variacoes_categorias"]:

    variacao = categoria["variacao"]

    if variacao is None:
        variacao_texto = "nova categoria"
    else:
        variacao_texto = f"{variacao:.2f}%"

    print(
        f"- {categoria['categoria']}: "
        f"atual = R$ {categoria['atual']:.2f} | "
        f"anterior = R$ {categoria['anterior']:.2f} | "
        f"variação = {variacao_texto}"
    )

print("\n========== PADRÕES IDENTIFICADOS ==========\n")

padroes = insight_service.identificar_padroes(
    analise
)

for padrao in padroes:
    print(padrao)

print("\n========== DADOS PARA IA ==========\n")

dados_ia = insight_service.preparar_dados_para_ia(
    analise
)

print(dados_ia)

print("\n========== ANÁLISE DIÁRIA ==========\n")

analise_diaria = insight_service.gerar_analise_diaria()

print(f"Período: {analise_diaria['periodo']}")

print(
    f"\nTotal atual: "
    f"R$ {analise_diaria['atual']['total']:.2f}"
)

print(
    f"Total anterior: "
    f"R$ {analise_diaria['anterior']['total']:.2f}"
)

variacao = analise_diaria["variacao_total"]

if variacao is None:
    print("Variação total: não é possível calcular")
else:
    print(
        f"Variação total: "
        f"{variacao:.2f}%"
    )

print("\nVariações por categoria:")

for categoria in analise_diaria["variacoes_categorias"]:

    variacao = categoria["variacao"]

    if variacao is None:
        variacao_texto = "nova categoria"
    else:
        variacao_texto = f"{variacao:.2f}%"

    print(
        f"- {categoria['categoria']}: "
        f"atual = R$ {categoria['atual']:.2f} | "
        f"anterior = R$ {categoria['anterior']:.2f} | "
        f"variação = {variacao_texto}"
    )

print("\n========== ANÁLISE MENSAL ==========")

analise_mensal = insight_service.gerar_analise_mensal()

print(f"\nPeríodo: {analise_mensal['periodo']}")

print(
    f"\nTotal atual: "
    f"R$ {analise_mensal['atual']['total']:.2f}"
)

print(
    f"Total anterior: "
    f"R$ {analise_mensal['anterior']['total']:.2f}"
)

if analise_mensal["variacao_total"] is not None:
    print(
        f"Variação total: "
        f"{analise_mensal['variacao_total']:.2f}%"
    )
else:
    print("Variação total: não é possível calcular")

print("\nVariações por categoria:")

for categoria in analise_mensal["variacoes_categorias"]:
    variacao = categoria["variacao"]

    if variacao is None:
        texto_variacao = "nova categoria"
    else:
        texto_variacao = f"{variacao:.2f}%"

    print(
        f"- {categoria['categoria']}: "
        f"atual = R$ {categoria['atual']:.2f} | "
        f"anterior = R$ {categoria['anterior']:.2f} | "
        f"variação = {texto_variacao}"
    )

print("\n========== CONFIGURAÇÃO DE INSIGHTS ==========\n")

print("Configuração inicial:")

configuracao = insight_service.obter_configuracao()

print(configuracao)


print("\nConfigurando frequência para DIARIO...")

insight_service.configurar_frequencia("DIARIO")

configuracao = insight_service.obter_configuracao()

print(configuracao)


print("\nConfigurando frequência para SEMANAL...")

insight_service.configurar_frequencia("SEMANAL")

configuracao = insight_service.obter_configuracao()

print(configuracao)


print("\nDesativando insights...")

insight_service.configurar_frequencia("NENHUM")

configuracao = insight_service.obter_configuracao()

print(configuracao)


print("\n========== DADOS PARA INSIGHT MANUAL ==========\n")

print("Insight diário:")

dados_diario = insight_service.gerar_dados_insight(
    "diario"
)

print(dados_diario)


print("\nInsight semanal:")

dados_semanal = insight_service.gerar_dados_insight(
    "semanal"
)

print(dados_semanal)


print("\nInsight mensal:")

dados_mensal = insight_service.gerar_dados_insight(
    "mensal"
)

print(dados_mensal)

print("\n========== TESTE DE ENVIO AUTOMÁTICO ==========\n")

print("Configurando frequência DIARIA...")

insight_service.configurar_frequencia("DIARIO")

configuracao = insight_service.obter_configuracao()

print("\nConfiguração:")
print(configuracao)

print(
    f"\nDeve gerar insight? "
    f"{insight_service.deve_gerar_insight()}"
)

print("\n========== TESTE APÓS ENVIO ==========\n")

print("Registrando envio do insight...")

database.registrar_envio_insight()

configuracao = insight_service.obter_configuracao()

print("\nConfiguração após envio:")
print(configuracao)

print(
    f"\nDeve gerar insight novamente? "
    f"{insight_service.deve_gerar_insight()}"
)

print("\n========== TESTE APÓS ENVIO ==========\n")

print("Registrando envio do insight...")

database.registrar_envio_insight()

configuracao = insight_service.obter_configuracao()

print("\nConfiguração após envio:")
print(configuracao)

print(
    f"\nDeve gerar insight novamente? "
    f"{insight_service.deve_gerar_insight()}"
)

print("\n========== TESTE SEMANAL ==========\n")

insight_service.configurar_frequencia("SEMANAL")

print("Configuração semanal:")
print(insight_service.obter_configuracao())

print(
    f"\nDeve gerar insight? "
    f"{insight_service.deve_gerar_insight()}"
)

print("\n========== TESTE APÓS 7 DIAS ==========\n")

database = insight_service.database

with database.conectar() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE configuracoes_insights
            SET ultimo_envio = CURRENT_TIMESTAMP - INTERVAL '8 days'
            WHERE telegram_id = %s
            """,
            (USUARIO_ID,),
        )

configuracao = insight_service.obter_configuracao()

print("Configuração após simulação:")
print(configuracao)

print(
    f"\nDeve gerar insight após 8 dias? "
    f"{insight_service.deve_gerar_insight()}"
)

# with database.conectar() as conn:
#     with conn.cursor() as cursor:
#         cursor.execute(
#             """
#             UPDATE configuracoes_insights
#             SET
#                 frequencia = 'SEMANAL',
#                 ativo = TRUE,
#                 horario = '09:00',
#                 ultimo_envio = %s
#             WHERE telegram_id = %s
#             """,
#             (
#                 datetime(2026, 8, 31, 9, 0),
#                 USUARIO_ID,
#             ),
#         )

print("\n========== TESTE DE AGENDAMENTO SEMANAL ==========")

insight_service.configurar_frequencia("SEMANAL")

# Segunda-feira às 08:59
segunda_0859 = datetime(2026, 9, 7, 8, 59)

print("\nSegunda-feira às 08:59:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(segunda_0859)
)

# Segunda-feira às 09:00
segunda_0900 = datetime(2026, 9, 7, 9, 0)

print("\nSegunda-feira às 09:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(segunda_0900)
)

# Segunda-feira às 10:00
segunda_1000 = datetime(2026, 9, 7, 10, 0)

print("\nSegunda-feira às 10:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(segunda_1000)
)

# Terça-feira às 09:00
terca_0900 = datetime(2026, 9, 8, 9, 0)

print("\nTerça-feira às 09:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(terca_0900)
)

print("\n========== TESTE APÓS ENVIO SEMANAL ==========")

# Simula que o insight foi enviado na segunda-feira às 09:00
with database.conectar() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE configuracoes_insights
            SET ultimo_envio = %s
            WHERE telegram_id = %s
            """,
            (
                datetime(2026, 9, 7, 9, 0),
                USUARIO_ID,
            ),
        )

# Verifica novamente na segunda-feira às 10:00
segunda_1000_apos_envio = datetime(2026, 9, 7, 10, 0)

print("\nSegunda-feira às 10:00, após envio às 09:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(
        segunda_1000_apos_envio
    )
)

# Verifica na terça-feira
terca_0900_apos_envio = datetime(2026, 9, 8, 9, 0)

print("\nTerça-feira às 09:00, após envio na segunda:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(
        terca_0900_apos_envio
    )
)

# Verifica na próxima segunda-feira
proxima_segunda = datetime(2026, 9, 14, 9, 0)

print("\nPróxima segunda-feira às 09:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(
        proxima_segunda
    )
)

print("\n========== TESTE DE AGENDAMENTO DIÁRIO ==========")

# Configura insights diários
insight_service.configurar_frequencia("DIARIO")

# Simula último envio no dia anterior
with database.conectar() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE configuracoes_insights
            SET
                horario = '09:00',
                ultimo_envio = %s
            WHERE telegram_id = %s
            """,
            (
                datetime(2026, 9, 7, 9, 0),
                USUARIO_ID,
            ),
        )

# Hoje às 08:59
diario_0859 = datetime(2026, 9, 8, 8, 59)

print("\nTerça-feira às 08:59:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(diario_0859)
)

# Hoje às 09:00
diario_0900 = datetime(2026, 9, 8, 9, 0)

print("\nTerça-feira às 09:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(diario_0900)
)

# Simula que enviou às 09:00
with database.conectar() as conn:
    with conn.cursor() as cursor:
        cursor.execute(
            """
            UPDATE configuracoes_insights
            SET ultimo_envio = %s
            WHERE telegram_id = %s
            """,
            (
                datetime(2026, 9, 8, 9, 0),
                USUARIO_ID,
            ),
        )

# Hoje às 10:00, depois do envio
diario_1000_apos_envio = datetime(2026, 9, 8, 10, 0)

print("\nTerça-feira às 10:00, após envio às 09:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(
        diario_1000_apos_envio
    )
)

# Dia seguinte
diario_dia_seguinte = datetime(2026, 9, 9, 9, 0)

print("\nQuarta-feira às 09:00:")
print(
    "Deve gerar insight?",
    insight_service.deve_gerar_insight(
        diario_dia_seguinte
    )
)

print("\n========== TESTE DE CONFIGURAÇÕES ATIVAS ==========")

configuracoes = database.listar_configuracoes_insights_ativas()

for configuracao in configuracoes:
    print(configuracao)