from datetime import datetime

from src.services.financial_summary_service import FinancialSummaryService


class FakeDatabase:
    def listar_compras(self, data_inicio=None, data_fim=None):
        if data_inicio.month == 9:
            return [
                (1, "Mercado", "Alimentação", "Carteira", 120.0, data_inicio),
                (2, "Ônibus", "Transporte", "Carteira", 30.0, data_inicio),
            ]
        return [(3, "Mercado", "Alimentação", "Carteira", 100.0, data_inicio)]

    def listar_contas(self):
        return [
            (1, "Carteira", "CARTEIRA", 300.0, None, True),
            (2, "Banco", "CONTA_CORRENTE", 150.0, None, True),
        ]


def test_calcula_resumo_mensal_com_projecao_e_categorias():
    resumo = FinancialSummaryService(FakeDatabase()).calcular_resumo_mensal(
        datetime(2026, 9, 15, 12, 0)
    )

    assert resumo["total_gasto"] == 150.0
    assert resumo["quantidade_compras"] == 2
    assert resumo["saldo_total"] == 450.0
    assert resumo["media_diaria"] == 10.0
    assert resumo["projecao_mensal"] == 300.0
    assert resumo["dias_cobertura_saldo"] == 45.0
    assert resumo["mes_anterior"] == {"total_gasto": 100.0, "variacao_percentual": 50.0}
    assert resumo["gastos_por_categoria"][0] == {
        "categoria": "Alimentação", "total": 120.0, "percentual": 80.0
    }


def test_variacao_sem_base_anterior_nao_inventa_percentual():
    assert FinancialSummaryService._variacao_percentual(10, 0) is None
    assert FinancialSummaryService._variacao_percentual(0, 0) == 0.0
