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


@pytest.mark.parametrize("texto", [
    "Abra o menu", "Pluto, me mostra o menu, por favor",
    "Como eu acesso o menu?", "Como faço para acessar o menu?",
    "Onde fica o menu?", "Quais são as opções do menu?", "menu",
])
def test_pedido_explicito_de_menu(texto):
    assert SkillRouter().selecionar(texto).info.nome == "abrir_menu"


@pytest.mark.parametrize("texto", [
    "Não abra o menu", "O menu ficou bonito", "O que significa menu?",
    "Ele disse: abra o menu", "Quando eu abro o menu ele trava",
    "Se eu pedir para abrir o menu, o que acontece?",
    "O menu do restaurante está caro", "Não quero ver o menu",
])
def test_mencao_ao_menu_nao_navega(texto):
    assert SkillRouter().selecionar(texto) is None


def test_pedido_menu_envia_botoes_reais():
    bot, update, context = _mensagem_bot("Como acesso o menu?")
    context.user_data["modo_conversa"] = True
    asyncio.run(bot.receber_mensagem(update, context))
    enviada = update.message.reply_text.call_args
    assert enviada.kwargs["reply_markup"] == bot._criar_menu_principal()
    assert "/menu" in enviada.args[0]
    bot._responder_conversa_financeira.assert_not_awaited()


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
    bot, update, context = _mensagem_bot("Registre a compra de pão por R$ 12")
    _ativar_interpretacao(bot, "registrar_compra")
    compra_service = Mock()
    compra_service.processar_compra.return_value = {"descricao": "pão", "valor": 12}
    monkeypatch.setattr(
        "src.telegram.telegram_bot.CompraService", Mock(return_value=compra_service)
    )

    asyncio.run(bot.receber_mensagem(update, context))

    compra_service.processar_compra.assert_called_once_with(
        mensagem="Registre a compra de pão por R$ 12"
    )
    bot._enviar_confirmacao.assert_awaited_once()
    bot.conversation_service.interpretar.assert_called_once()


def test_pedido_para_registrar_compra_solicita_descricao(monkeypatch):
    bot, update, context = _mensagem_bot("Quero registrar uma compra")
    _ativar_interpretacao(bot, "iniciar_registro_compra")
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


@pytest.mark.parametrize("perfil", [None, {"objetivo": "organizar gastos"}])
def test_falar_com_pluto_abre_conversa_sem_entrevista(perfil):
    bot = TelegramBot.__new__(TelegramBot)
    bot._responder_callback = AsyncMock(return_value=True)
    query = SimpleNamespace(data="menu:conversa", edit_message_text=AsyncMock())
    update = SimpleNamespace(callback_query=query)
    context = SimpleNamespace(user_data={
        "entrevista_financeira": {"indice": 1, "respostas": ["economizar"]},
    })
    if perfil:
        context.user_data["perfil_financeiro"] = perfil

    asyncio.run(bot.menu_callback(update, context))

    assert context.user_data["modo_conversa"] is True
    assert "entrevista_financeira" not in context.user_data
    assert context.user_data.get("perfil_financeiro") == perfil
    assert "Sobre o que" in query.edit_message_text.call_args.args[0]


@pytest.mark.parametrize("entrevista_antiga", [False, True])
def test_pergunta_geral_e_respondida_sem_renda(entrevista_antiga):
    bot, update, context = _mensagem_bot("O que são juros compostos?")
    context.user_data["modo_conversa"] = True
    if entrevista_antiga:
        context.user_data["entrevista_financeira"] = {"indice": 1, "respostas": ["oi"]}

    asyncio.run(bot.receber_mensagem(update, context))

    bot._responder_conversa_financeira.assert_awaited_once_with(
        update, context, update.message.text
    )
    assert "entrevista_financeira" not in context.user_data
    assert "perfil_financeiro" not in context.user_data


def test_pedido_de_plano_continua_solicitando_salario():
    bot, update, context = _mensagem_bot("Quero economizar")
    _ativar_interpretacao(bot, "planejar_economia")
    context.user_data["modo_conversa"] = True

    asyncio.run(bot.receber_mensagem(update, context))

    assert context.user_data["planejamento_economia"] is True
    assert "salário líquido" in update.message.reply_text.call_args.args[0]
    bot.conversation_service.interpretar.assert_called_once()


def _ativar_interpretacao(bot, skill=None):
    bot.conversation_service = Mock()
    bot.conversation_service.interpretar.return_value = {
        "skill": skill, "resposta": "Vamos conversar sobre isso.",
    }
    bot.financial_context_service = Mock()
    bot.financial_context_service.obter.return_value = {}
    bot._responder_conversa_financeira = (
        TelegramBot._responder_conversa_financeira.__get__(bot, TelegramBot)
    )


@pytest.mark.parametrize("modo_conversa", [False, True])
@pytest.mark.parametrize("texto", [
    "Comprei um celular e me arrependi",
    "Vale a pena comprar um carro?",
    "Comprei pão por R$ 12, você acha caro?",
    "Não quero registrar uma compra",
    "Como posso registrar uma compra?",
    "Meu amigo disse que comprou uma casa",
    "Se eu comprar isso vou ficar sem dinheiro",
    "Comprei pão por R$ 12",
])
def test_mencoes_de_compra_passam_por_intencao_sem_iniciar_cadastro(
    monkeypatch, modo_conversa, texto
):
    bot, update, context = _mensagem_bot(texto)
    context.user_data["modo_conversa"] = modo_conversa
    historico = [{"role": "user", "content": "Quero conversar sobre consumo"}]
    context.user_data["historico_assistente"] = historico.copy()
    _ativar_interpretacao(bot)
    compra_service = Mock()
    monkeypatch.setattr("src.telegram.telegram_bot.CompraService", compra_service)

    asyncio.run(bot.receber_mensagem(update, context))

    bot.conversation_service.interpretar.assert_called_once()
    assert bot.conversation_service.interpretar.call_args.args[0] == texto
    assert bot.conversation_service.interpretar.call_args.args[4][0] == historico[0]
    compra_service.assert_not_called()
    bot._enviar_confirmacao.assert_not_awaited()
    assert "aguardando_descricao_compra" not in context.user_data
    assert "compra_pendente" not in context.user_data
    update.message.reply_text.assert_awaited_once_with("Vamos conversar sobre isso.")

@pytest.mark.parametrize("entrada", ["menu", "start", "voltar", "conversa", "texto"])
def test_navegacao_abandona_compra_pendente_e_libera_conversa(entrada):
    bot, update, context = _mensagem_bot("Quero conversar sobre consumo")
    bot._responder_callback = AsyncMock(return_value=True)
    bot._processar_descricao_compra = AsyncMock()
    perfil = {"objetivo": "economizar"}
    historico = [{"role": "user", "content": "Olá"}]
    context.user_data.update({
        "aguardando_descricao_compra": True,
        "compra_pendente": {"descricao": "rascunho", "valor": 12},
        "criando_conta": True,
        "criando_categoria": True,
        "editando_compra": {"id": 1, "campo": "valor"},
        "movimentacao_saldo": {"tipo": "deposito"},
        "perfil_financeiro": perfil,
        "historico_assistente": historico,
    })

    async def executar():
        if entrada in {"menu", "start"}:
            await getattr(bot, entrada)(update, context)
        elif entrada == "texto":
            update.message.text = "Abra o menu"
            await bot.receber_mensagem(update, context)
            update.message.text = "Quero conversar sobre consumo"
        else:
            update.callback_query = SimpleNamespace(
                data="menu:principal" if entrada == "voltar" else "menu:conversa",
                edit_message_text=AsyncMock(),
            )
            await bot.menu_callback(update, context)
        await bot.receber_mensagem(update, context)

    asyncio.run(executar())

    bot._processar_descricao_compra.assert_not_awaited()
    bot._responder_conversa_financeira.assert_awaited_once_with(
        update, context, "Quero conversar sobre consumo"
    )
    assert "compra_pendente" not in context.user_data
    assert "aguardando_descricao_compra" not in context.user_data
    assert context.user_data["perfil_financeiro"] == perfil
    assert context.user_data["historico_assistente"] == historico


def test_botao_registrar_compra_ativa_descricao_somente_apos_escolha():
    bot, update, context = _mensagem_bot("Pão por 12 reais")
    bot._responder_callback = AsyncMock(return_value=True)
    bot._processar_descricao_compra = AsyncMock()
    update.callback_query = SimpleNamespace(
        data="menu:compra", edit_message_text=AsyncMock(),
    )

    async def executar():
        await bot.menu_callback(update, context)
        assert context.user_data["aguardando_descricao_compra"] is True
        await bot.receber_mensagem(update, context)

    asyncio.run(executar())

    bot._processar_descricao_compra.assert_awaited_once_with(
        update, context, "Pão por 12 reais"
    )
    bot._responder_conversa_financeira.assert_not_awaited()

@pytest.mark.parametrize("pedido", ["quero acessar o menu", "menu"])
def test_pedido_menu_interrompe_coleta_salario_da_captura(pedido):
    bot, update, context = _mensagem_bot(pedido)
    bot._continuar_planejamento_economia = AsyncMock()
    context.user_data["planejamento_economia"] = True

    asyncio.run(bot.receber_mensagem(update, context))

    assert "planejamento_economia" not in context.user_data
    bot._continuar_planejamento_economia.assert_not_awaited()
    assert update.message.reply_text.call_args.kwargs["reply_markup"] == (
        bot._criar_menu_principal()
    )

    update.message.text = "Gostaria de conversar"
    asyncio.run(bot.receber_mensagem(update, context))
    bot._responder_conversa_financeira.assert_awaited_once_with(
        update, context, "Gostaria de conversar"
    )


@pytest.mark.parametrize("modo_conversa", [False, True])
@pytest.mark.parametrize("texto", [
    "como montar um plano de finanças",
    "como funciona um planejamento financeiro?",
    "quero entender como economizar sem fazer um plano agora",
])
def test_duvida_planejamento_passa_pela_intencao_sem_entrevista(modo_conversa, texto):
    bot, update, context = _mensagem_bot(texto)
    context.user_data["modo_conversa"] = modo_conversa
    _ativar_interpretacao(bot)
    bot.iniciar_planejamento_economia = AsyncMock()

    asyncio.run(bot.receber_mensagem(update, context))

    bot.conversation_service.interpretar.assert_called_once()
    bot.iniciar_planejamento_economia.assert_not_awaited()
    assert "planejamento_economia" not in context.user_data
    update.message.reply_text.assert_awaited_once_with("Vamos conversar sobre isso.")