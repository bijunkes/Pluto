from __future__ import annotations

from .base import Skill, SkillInfo, padrao


class ListarComprasSkill(Skill):
    info = SkillInfo(
        "listar_compras", "Lista e filtra as compras registradas.",
        ("mostre minhas compras", "quais foram meus gastos?"),
    )
    prioridade = 30
    padroes = (
        padrao(r"\b(listar?|mostr[ae]|ver|quais?)\b.*\b(compras?|gastos?|despesas?)\b"),
        padrao(r"\b(minhas? compras?|meus gastos?|historico de compras?)\b"),
    )

    async def executar(self, bot, update, context):
        await bot.listar_compras(update, context)


class ListarContasSkill(Skill):
    info = SkillInfo(
        "listar_contas", "Mostra contas e saldos.",
        ("mostre minhas contas", "qual é meu saldo?"),
    )
    prioridade = 30
    padroes = (
        padrao(r"\b(listar?|mostr[ae]|ver|quais?)\b.*\b(contas?|saldos?)\b"),
        padrao(r"\b(minhas? contas?|meu saldo)\b"),
    )

    async def executar(self, bot, update, context):
        await bot.listar_contas(update, context)


class CriarCategoriaSkill(Skill):
    info = SkillInfo(
        "criar_categoria", "Inicia a criacao de uma categoria.",
        ("quero criar uma categoria",),
    )
    prioridade = 40
    padroes = (padrao(r"\b(criar|crie|cria|adicion[ae]|nova)\b.*\bcategoria\b"),)

    async def executar(self, bot, update, context):
        await bot.criar_categoria(update, context)


class CriarContaSkill(Skill):
    info = SkillInfo(
        "criar_conta", "Inicia o cadastro de uma conta financeira.",
        ("quero criar uma conta",),
    )
    prioridade = 40
    padroes = (padrao(r"\b(criar|crie|cria|adicion[ae]|nova)\b.*\bconta\b"),)

    async def executar(self, bot, update, context):
        await bot.criar_conta(update, context)


class DashboardSkill(Skill):
    info = SkillInfo(
        "abrir_dashboard", "Gera o acesso seguro ao dashboard.",
        ("abra o dashboard",),
    )
    prioridade = 20
    padroes = (padrao(r"\b(dashboard|painel|relatorio)\b"),)

    async def executar(self, bot, update, context):
        await bot.abrir_dashboard(update, context)


class AjudaSkill(Skill):
    info = SkillInfo(
        "ajuda", "Explica o que o assistente consegue fazer.",
        ("o que você sabe fazer?", "preciso de ajuda"),
    )
    prioridade = 10
    padroes = (
        padrao(r"\b(ajuda|help|capacidades|habilidades)\b"),
        padrao(r"\bo que (voce )?(faz|sabe fazer|consegue fazer)\b"),
    )

    async def executar(self, bot, update, context):
        await bot.help(update, context)


class RegistrarCompraSkill(Skill):
    info = SkillInfo(
        "registrar_compra", "Entende uma compra e prepara seu registro.",
        ("comprei um tênis por R$ 200", "gastei 35 reais no mercado"),
    )
    prioridade = 5
    padroes = (
        padrao(r"\b(comprei|gastei|paguei|custou|compra|despesa)\b"),
        padrao(r"\b(r\$|reais?)\s*\d"),
    )

    async def executar(self, bot, update, context):
        await bot.executar_registro_compra(update, context)


class PlanejarEconomiaSkill(Skill):
    info = SkillInfo(
        "planejar_economia", "Calcula quanto gastar e guardar por mês.",
        ("quero guardar dinheiro", "me ajude a economizar"),
    )
    prioridade = 50
    padroes = (
        padrao(r"\b(quero|preciso|gostaria|me ajud[ae])\b.*\b(guardar|economizar|poupar)\b"),
        padrao(r"\b(plano|planejamento)\b.*\b(economia|financeiro|guardar|poupar)\b"),
    )

    async def executar(self, bot, update, context):
        await bot.iniciar_planejamento_economia(update, context)


SKILLS_PADRAO = (
    PlanejarEconomiaSkill,
    CriarCategoriaSkill,
    CriarContaSkill,
    ListarComprasSkill,
    ListarContasSkill,
    DashboardSkill,
    AjudaSkill,
    RegistrarCompraSkill,
)
