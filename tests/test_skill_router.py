import asyncio

import pytest

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
