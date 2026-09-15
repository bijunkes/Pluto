from datetime import datetime

from src.services.financial_context_service import FinancialContextService


class DatabaseFake:
    def __init__(self, usuario_id):
        self.usuario_id = usuario_id

    def listar_contas(self):
        return [(1, "Banco", "CONTA_CORRENTE", 900, None, True)]

    def listar_compras(self):
        return [
            (1, "Mercado", "Alimentacao", "Banco", 100, datetime(2026, 9, 1)),
            (2, "Livro", "Educacao", "Banco", 50, datetime(2026, 9, 2)),
        ]


def test_monta_contexto_financeiro(monkeypatch):
    monkeypatch.setattr(
        "src.services.financial_context_service.Database", DatabaseFake
    )
    contexto = FinancialContextService().obter(42)

    assert contexto["total_no_escopo"] == 150
    assert contexto["totais_por_categoria"]["Alimentacao"] == 100
    assert contexto["contas"][0]["saldo"] == 900
    assert len(contexto["compras"]) == 2
