import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, Mock

from src.database.database import Database
from src.services.scheduler_service import SchedulerService


def test_envia_texto_e_registra_somente_apos_sucesso(monkeypatch):
    lancamento = datetime(2026, 10, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(Database, "listar_lembretes_gastos_pendentes", lambda: [(123, lancamento)])
    registrar = Mock()
    monkeypatch.setattr(Database, "registrar_envio_lembrete_gastos", registrar)
    envio = AsyncMock()
    scheduler = SchedulerService.__new__(SchedulerService)

    assert asyncio.run(scheduler.processar_lembretes_gastos(envio)) == [123]
    envio.assert_awaited_once_with(123, "Ei, você já lançou seus gastos?")
    registrar.assert_called_once_with(lancamento)


def test_falha_de_envio_nao_registra_e_nao_impede_outros(monkeypatch):
    lancamento = datetime(2026, 10, 12, tzinfo=timezone.utc)
    monkeypatch.setattr(Database, "listar_lembretes_gastos_pendentes", lambda: [(123, lancamento), (456, lancamento)])
    registrar = Mock()
    monkeypatch.setattr(Database, "registrar_envio_lembrete_gastos", registrar)
    envio = AsyncMock(side_effect=[RuntimeError("Telegram indisponível"), None])
    scheduler = SchedulerService.__new__(SchedulerService)

    assert asyncio.run(scheduler.processar_lembretes_gastos(envio)) == [456]
    registrar.assert_called_once_with(lancamento)


def test_nenhum_pendente_nao_envia(monkeypatch):
    monkeypatch.setattr(Database, "listar_lembretes_gastos_pendentes", lambda: [])
    envio = AsyncMock()
    scheduler = SchedulerService.__new__(SchedulerService)
    assert asyncio.run(scheduler.processar_lembretes_gastos(envio)) == []
    envio.assert_not_awaited()


def test_compra_retroativa_reinicia_contagem_no_momento_do_registro(monkeypatch):
    database = Database(123)
    cursor = MagicMock()
    cursor.fetchone.return_value = (10,)
    cursor.rowcount = 1
    conn = MagicMock()
    conn.__enter__.return_value.cursor.return_value.__enter__.return_value = cursor
    monkeypatch.setattr(database, "conectar", lambda: conn)
    monkeypatch.setattr(database, "buscar_categoria", lambda _: (1,))
    monkeypatch.setattr(database, "buscar_conta", lambda _: (2, "Conta", "CORRENTE", 100, None, True))

    assert database.salvar_compra("Pão", "Comida", 2, 5, datetime(2020, 1, 1)) == 10
    sql, params = cursor.execute.call_args.args
    assert "CURRENT_TIMESTAMP" in sql
    assert "ultimo_envio = NULL" in sql
    assert params == (123,)
