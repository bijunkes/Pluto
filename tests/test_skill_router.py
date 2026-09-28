import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from src.telegram.telegram_bot import TelegramBot
from src.telegram.skills.base import Skill, SkillInfo, padrao
from src.telegram.skills.router import SkillRouter


@pytest.mark.parametrize(
    ("texto", "skill"),
    [
        ("Mostre minhas compras", "listar_compras"),
        ("Qual e o meu saldo?", "listar_contas"),
        ("Quero criar uma categoria", "criar_categoria"),
        ("Adicione uma nova conta", "criar_conta"),
        ("Abra meu dashboard", "abrir_dashboard"),
        ("O que voce sabe fazer?", "ajuda"),
        ("Gastei R$ 42 no mercado", "registrar_compra"),
        ("Quero registrar uma compra", "iniciar_registro_compra"),
        ("Quanto eu gastei esse mês?", "consultar_gastos_mes"),
        ("Qual foi meu total de gastos neste mês?", "consultar_gastos_mes"),
        ("Pluto, quero guardar dinheiro", "planejar_economia"),
        ("Me ajude a economizar", "planejar_economia"),
    ],
)
def test_seleciona_skill(texto, skill):
    selecionada = SkillRouter().selecionar(texto)
    assert selecionada is not None
    assert selecionada.info.nome == skill


def test_nao_trata_conversa_desconhecida_como_compra():
    assert SkillRouter().selecionar("como foi seu dia?") is None


def test_permite_registrar_nova_skill():
    class TesteSkill(Skill):
        info = SkillInfo("teste", "Skill de teste", ("teste",))
        padroes = (padrao(r"\bteste\b"),)

        async def executar(self, bot, update, context):
            bot.append("executada")

    router = SkillRouter([])
    router.registrar(TesteSkill())
    chamadas = []
    assert asyncio.run(router.executar("execute o teste", chamadas, None, None))
    assert chamadas == ["executada"]


def test_rejeita_nome_duplicado():
    router = SkillRouter()
    with pytest.raises(ValueError):
        router.registrar(router.skills[0])


def _mensagem_bot(texto):
    bot = TelegramBot.__new__(TelegramBot)
    bot.skill_router = SkillRouter()
    bot.ia_service = None
    bot._responder_conversa_financeira = AsyncMock()
    bot._enviar_confirmacao = AsyncMock()
    update = SimpleNamespace(
        message=SimpleNamespace(text=texto, reply_text=AsyncMock()),
        effective_user=SimpleNamespace(id=123),
    )
    context = SimpleNamespace(user_data={})
    return bot, update, context


@pytest.mark.parametrize("texto", ["oi", "Qual é a taxa Selic?"])
def test_mensagem_comum_vai_para_conversa(texto):
    bot, update, context = _mensagem_bot(texto)

    asyncio.run(bot.receber_mensagem(update, context))

    bot._responder_conversa_financeira.assert_awaited_once_with(
        update, context, texto
    )
    bot._enviar_confirmacao.assert_not_awaited()


def test_compra_explicita_continua_no_registro(monkeypatch):
    bot, update, context = _mensagem_bot("Comprei pão por R$ 12")
    compra_service = Mock()
    compra_service.processar_compra.return_value = {"descricao": "pão", "valor": 12}
    monkeypatch.setattr(
        "src.telegram.telegram_bot.CompraService", Mock(return_value=compra_service)
    )

    asyncio.run(bot.receber_mensagem(update, context))

    compra_service.processar_compra.assert_called_once_with(
        mensagem="Comprei pão por R$ 12"
    )
    bot._enviar_confirmacao.assert_awaited_once()
    bot._responder_conversa_financeira.assert_not_awaited()


def test_pedido_para_registrar_compra_solicita_descricao(monkeypatch):
    bot, update, context = _mensagem_bot("Quero registrar uma compra")
    compra_service = Mock()
    monkeypatch.setattr(
        "src.telegram.telegram_bot.CompraService", Mock(return_value=compra_service)
    )

    asyncio.run(bot.receber_mensagem(update, context))

    assert context.user_data["aguardando_descricao_compra"] is True
    update.message.reply_text.assert_awaited_once_with(
        "Descreva o que você quer registrar, incluindo o produto e o valor pago."
    )
    compra_service.processar_compra.assert_not_called()


def test_descricao_seguinte_e_analisada_como_compra(monkeypatch):
    bot, update, context = _mensagem_bot("um pão por 12 reais")
    context.user_data["aguardando_descricao_compra"] = True
    compra_service = Mock()
    compra_service.processar_compra.return_value = {"descricao": "pão", "valor": 12}
    monkeypatch.setattr(
        "src.telegram.telegram_bot.CompraService", Mock(return_value=compra_service)
    )

    asyncio.run(bot.receber_mensagem(update, context))

    assert "aguardando_descricao_compra" not in context.user_data
    compra_service.processar_compra.assert_called_once_with(
        mensagem="um pão por 12 reais"
    )
    bot._enviar_confirmacao.assert_awaited_once()


def test_consulta_mensal_nao_inicia_registro_de_compra(monkeypatch):
    bot, update, context = _mensagem_bot("Quanto eu gastei esse mês?")
    bot.consultar_gastos_mes_atual = AsyncMock()
    compra_service = Mock()
    monkeypatch.setattr(
        "src.telegram.telegram_bot.CompraService", Mock(return_value=compra_service)
    )

    asyncio.run(bot.receber_mensagem(update, context))

    bot.consultar_gastos_mes_atual.assert_awaited_once_with(update, context)
    compra_service.processar_compra.assert_not_called()
    bot._enviar_confirmacao.assert_not_awaited()


def test_consulta_mensal_responde_total_formatado(monkeypatch):
    bot, update, context = _mensagem_bot("Quanto eu gastei esse mês?")
    compra_service = Mock()
    compra_service.database = Mock()
    monkeypatch.setattr(
        "src.telegram.telegram_bot.CompraService", Mock(return_value=compra_service)
    )
    resumo_service = Mock()
    resumo_service.calcular_resumo_mensal.return_value = {
        "periodo": {"inicio": datetime(2026, 9, 1)},
        "total_gasto": 1234.5,
        "quantidade_compras": 2,
    }
    monkeypatch.setattr(
        "src.telegram.telegram_bot.FinancialSummaryService",
        Mock(return_value=resumo_service),
    )

    asyncio.run(bot.consultar_gastos_mes_atual(update, context))

    update.message.reply_text.assert_awaited_once_with(
        "💰 Em setembro de 2026, você gastou R$ 1.234,50 em 2 compras registradas."
    )


def test_comando_menu_mostra_opcoes():
    bot, update, context = _mensagem_bot("/menu")

    asyncio.run(bot.menu(update, context))

    resposta = update.message.reply_text.await_args
    callbacks = [
        botao.callback_data
        for linha in resposta.kwargs["reply_markup"].inline_keyboard
        for botao in linha
    ]
    assert "menu:conversa" in callbacks
    assert "menu:compra" in callbacks


def test_cadastro_de_conta_tem_prioridade_sobre_conversa():
    bot, update, context = _mensagem_bot("Conta principal")
    context.user_data["criando_conta"] = True

    asyncio.run(bot.receber_mensagem(update, context))

    assert context.user_data["nome_conta_pendente"] == "Conta principal"
    assert context.user_data["etapa_criacao_conta"] == "tipo"
    bot._responder_conversa_financeira.assert_not_awaited()


def test_cadastro_de_categoria_tem_prioridade_sobre_conversa(monkeypatch):
    bot, update, context = _mensagem_bot("Alimentação")
    context.user_data["criando_categoria"] = True
    compra_service = Mock()
    monkeypatch.setattr(
        "src.telegram.telegram_bot.CompraService", Mock(return_value=compra_service)
    )

    asyncio.run(bot.receber_mensagem(update, context))

    compra_service.adicionar_categoria.assert_called_once_with("Alimentação")
    assert "criando_categoria" not in context.user_data
    bot._responder_conversa_financeira.assert_not_awaited()


def test_estados_do_usuario_sao_persistidos(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "TELEGRAM_BOT_TOKEN", "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi"
    )
    monkeypatch.setattr("src.telegram.telegram_bot.IAService", Mock())
    monkeypatch.setattr("src.telegram.telegram_bot.SchedulerService", Mock())
    monkeypatch.setattr("src.telegram.telegram_bot.FinancialContextService", Mock())
    monkeypatch.setattr(
        "src.telegram.telegram_bot.__file__",
        str(tmp_path / "src" / "telegram" / "telegram_bot.py"),
    )

    bot = TelegramBot()

    assert bot.app.persistence.filepath == tmp_path / "data" / "telegram_state.pickle"
    assert bot.app.persistence.store_data.user_data is True
    assert bot.app.persistence.store_data.chat_data is False
