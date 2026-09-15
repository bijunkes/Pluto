import calendar
from datetime import datetime


class FinancialSummaryService:
    """Calcula indicadores financeiros a partir de compras e contas."""

    def __init__(self, database):
        self.database = database

    @staticmethod
    def _inicio_mes(referencia):
        return referencia.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _mes_anterior(inicio_mes):
        if inicio_mes.month == 1:
            return inicio_mes.replace(year=inicio_mes.year - 1, month=12)
        return inicio_mes.replace(month=inicio_mes.month - 1)

    @staticmethod
    def _variacao_percentual(atual, anterior):
        if anterior > 0:
            return round(((atual - anterior) / anterior) * 100, 2)
        if atual == 0:
            return 0.0
        return None

    def calcular_resumo_mensal(self, agora=None):
        agora = agora or datetime.now()
        inicio_atual = self._inicio_mes(agora)
        inicio_anterior = self._mes_anterior(inicio_atual)

        compras_atuais = self.database.listar_compras(inicio_atual, agora)
        compras_anteriores = self.database.listar_compras(inicio_anterior, inicio_atual)
        contas = self.database.listar_contas()

        total_atual = round(sum(float(compra[4]) for compra in compras_atuais), 2)
        total_anterior = round(sum(float(compra[4]) for compra in compras_anteriores), 2)
        saldo_total = round(sum(float(conta[3]) for conta in contas), 2)

        dias_decorridos = agora.day
        dias_no_mes = calendar.monthrange(agora.year, agora.month)[1]
        media_diaria = round(total_atual / dias_decorridos, 2)
        projecao_mensal = round(media_diaria * dias_no_mes, 2)
        dias_cobertura = (
            round(saldo_total / media_diaria, 1)
            if media_diaria > 0 and saldo_total >= 0
            else None
        )

        categorias = {}
        for compra in compras_atuais:
            nome = str(compra[2])
            categorias[nome] = categorias.get(nome, 0.0) + float(compra[4])

        gastos_por_categoria = [
            {
                "categoria": nome,
                "total": round(valor, 2),
                "percentual": round((valor / total_atual) * 100, 2) if total_atual > 0 else 0.0,
            }
            for nome, valor in sorted(categorias.items(), key=lambda item: item[1], reverse=True)
        ]

        return {
            "periodo": {"inicio": inicio_atual, "fim": agora},
            "total_gasto": total_atual,
            "quantidade_compras": len(compras_atuais),
            "saldo_total": saldo_total,
            "media_diaria": media_diaria,
            "projecao_mensal": projecao_mensal,
            "dias_cobertura_saldo": dias_cobertura,
            "mes_anterior": {
                "total_gasto": total_anterior,
                "variacao_percentual": self._variacao_percentual(total_atual, total_anterior),
            },
            "gastos_por_categoria": gastos_por_categoria,
        }
