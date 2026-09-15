import asyncio
from decimal import Decimal

import pytest

from src.services.savings_plan_service import SavingsPlanService
from src.telegram.telegram_bot import TelegramBot


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("R$ 3.000,00", Decimal("3000.00")),
        ("2500", Decimal("2500.00")),
        ("1.234,56 reais", Decimal("1234.56")),
    ],
)
def test_interpreta_salario_em_formatos_comuns(texto, esperado):
    assert SavingsPlanService.interpretar_valor(texto) == esperado


def test_calcula_plano_50_30_20():
    assert SavingsPlanService.calcular(3000) == {
        "salario": Decimal("3000.00"),
        "necessidades": Decimal("1500.00"),
        "desejos": Decimal("900.00"),
        "guardar": Decimal("600.00"),
    }


@pytest.mark.parametrize("valor", ["abc", "0", "-100"])
def test_rejeita_salario_invalido(valor):
    with pytest.raises(ValueError):
        SavingsPlanService.interpretar_valor(valor)


class FakeMessage:
    def __init__(self):
        self.respostas = []

    async def reply_text(self, texto, **kwargs):
        self.respostas.append(texto)


class FakeUpdate:
    def __init__(self):
        self.message = FakeMessage()
        self.callback_query = None


class FakeContext:
    def __init__(self):
        self.user_data = {}


def test_fluxo_pergunta_salario_e_entrega_plano():
    bot = TelegramBot.__new__(TelegramBot)
    update = FakeUpdate()
    context = FakeContext()

    asyncio.run(bot.iniciar_planejamento_economia(update, context))
    assert context.user_data["planejamento_economia"] is True
    assert "salário líquido" in update.message.respostas[-1]

    asyncio.run(
        bot._continuar_planejamento_economia(update, context, "R$ 3.000,00")
    )
    resposta = update.message.respostas[-1]
    assert "R$ 1.500,00" in resposta
    assert "R$ 900,00" in resposta
    assert "R$ 600,00" in resposta
    assert "planejamento_economia" not in context.user_data


def test_menu_principal_oferece_conversa_com_pluto():
    bot = TelegramBot.__new__(TelegramBot)

    menu = bot._criar_menu_principal()

    callbacks = [
        botao.callback_data
        for linha in menu.inline_keyboard
        for botao in linha
    ]
    assert "menu:conversa" in callbacks


def test_criar_conta_tambem_funciona_por_mensagem():
    bot = TelegramBot.__new__(TelegramBot)
    update = FakeUpdate()
    context = FakeContext()

    asyncio.run(bot.criar_conta(update, context))

    assert context.user_data["criando_conta"] is True
    assert "Digite o nome da conta" in update.message.respostas[-1]
