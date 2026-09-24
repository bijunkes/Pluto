import os
import asyncio

from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler,
)

from src.services.ia_service import IAService
from src.services.compra_service import CompraService
from src.services.exceptions import AnaliseIAError
from src.services.auth_service import gerar_link_login

from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from src.database.database import Database

from src.services.scheduler_service import SchedulerService
from src.services.savings_plan_service import SavingsPlanService
from src.services.conversation_service import ConversationService
from src.services.financial_context_service import FinancialContextService
from src.telegram.skills import SkillRouter


class TelegramBot:

    PERGUNTAS_ENTREVISTA = (
        "1/3 — Qual é o seu principal objetivo financeiro neste momento?",
        "2/3 — Como você descreveria sua renda, seus gastos mensais e eventuais dívidas?",
        "3/3 — Quanto você já conhece sobre finanças e investimentos, e como lida com riscos?",
    )

    def __init__(self):

        load_dotenv()

        self.token = os.environ["TELEGRAM_BOT_TOKEN"]

        # Serviço de IA com failover entre Gemini e Groq
        self.ia_service = IAService()

        # Scheduler dos insights automáticos
        self.scheduler_service = SchedulerService(self.ia_service)

        # Seleciona ações do bot a partir de frases em linguagem natural.
        self.skill_router = SkillRouter()
        self.conversation_service = None
        self.financial_context_service = FinancialContextService()

        # Aplicação do Telegram
        self.app = Application.builder().token(self.token).build()

        # Registra todos os comandos
        self._configurar_handlers()

    def _configurar_handlers(self):

        # Comando para iniciar o bot
        self.app.add_handler(CommandHandler("start", self.start))

        # Menu principal
        self.app.add_handler(CommandHandler("menu", self.menu))

        self.app.add_handler(
            CallbackQueryHandler(self.menu_callback, pattern="^menu:")
        )

        # Envia o link de acesso ao dashboard web
        self.app.add_handler(CommandHandler("dashboard", self.abrir_dashboard))

        # Comando de ajuda
        self.app.add_handler(CommandHandler("help", self.help))

        # Recebe fotos do usuário
        self.app.add_handler(MessageHandler(filters.PHOTO, self.receber_foto))

        # Receve mensagens de texto
        self.app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.receber_mensagem)
        )

        # Confirma a compra
        self.app.add_handler(
            CallbackQueryHandler(self.confirmar_compra, pattern="^confirmar$")
        )

        # Lista as compras do usuário
        self.app.add_handler(CommandHandler("compras", self.listar_compras))

        # Lista as contas do usuário
        self.app.add_handler(
            CommandHandler("contas", self.listar_contas)
        )
        self.app.add_handler(CommandHandler("categorias", self.listar_categorias))
        self.app.add_handler(CommandHandler("insights", self.insights))

        # Insights e configuração das notificações
        self.app.add_handler(CallbackQueryHandler(self.insights_callback, pattern="^insights:"))

        self.app.add_handler(
            CallbackQueryHandler(self.compras_callback, pattern="^compras:")
        )
        self.app.add_handler(
            CallbackQueryHandler(self.editar_compras_lista, pattern="^compras:editar$")
        )

        # Cancela a compra
        self.app.add_handler(
            CallbackQueryHandler(self.cancelar_compra, pattern="^cancelar$")
        )

        # Cria categoria
        self.app.add_handler(CallbackQueryHandler(self.compra_item, pattern="^compra_item:"))
        self.app.add_handler(CallbackQueryHandler(self.conta_item, pattern="^conta_item:"))
        self.app.add_handler(CallbackQueryHandler(self.iniciar_adicionar_saldo, pattern="^saldo:adicionar$"))
        self.app.add_handler(CallbackQueryHandler(self.iniciar_retirar_saldo, pattern="^saldo:retirar$"))
        self.app.add_handler(CallbackQueryHandler(self.iniciar_transferencia, pattern="^saldo:transferir$"))
        self.app.add_handler(CallbackQueryHandler(self.selecionar_conta_movimentacao, pattern="^saldo_conta:"))
        self.app.add_handler(CallbackQueryHandler(self.selecionar_destino_transferencia, pattern="^saldo_destino:"))
        self.app.add_handler(CallbackQueryHandler(self.selecionar_origem_transferencia, pattern="^saldo_origem:"))
        self.app.add_handler(CallbackQueryHandler(self.confirmar_movimentacao_saldo, pattern="^confirmar_saldo:"))
        self.app.add_handler(CallbackQueryHandler(self.cancelar_movimentacao_saldo, pattern="^cancelar_saldo$"))
        self.app.add_handler(CallbackQueryHandler(self.categoria_item, pattern="^categoria_item:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_compra, pattern="^editar_compra:"))
        self.app.add_handler(CallbackQueryHandler(self.excluir_compra, pattern="^excluir_compra:"))
        self.app.add_handler(CallbackQueryHandler(self.confirmar_exclusao_compra, pattern="^confirmar_exclusao_compra:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_compra_campo, pattern="^editar_compra_campo:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_compra_categoria, pattern="^editar_compra_categoria:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_compra_conta, pattern="^editar_compra_conta:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_conta, pattern="^editar_conta:"))
        self.app.add_handler(CallbackQueryHandler(self.excluir_conta, pattern="^excluir_conta:"))
        self.app.add_handler(CallbackQueryHandler(self.confirmar_exclusao_conta, pattern="^confirmar_exclusao_conta:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_conta_nome, pattern="^editar_conta_nome:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_conta_tipo, pattern="^editar_conta_tipo:"))
        self.app.add_handler(CallbackQueryHandler(self.salvar_conta_tipo, pattern="^salvar_conta_tipo:"))
        self.app.add_handler(CallbackQueryHandler(self.editar_categoria, pattern="^editar_categoria:"))
        self.app.add_handler(CallbackQueryHandler(self.excluir_categoria, pattern="^excluir_categoria:"))
        self.app.add_handler(CallbackQueryHandler(self.confirmar_exclusao_categoria, pattern="^confirmar_exclusao_categoria:"))

        self.app.add_handler(
            CallbackQueryHandler(self.criar_categoria, pattern="^criar_categoria$")
        )

        # Seleciona categoria
        self.app.add_handler(
            CallbackQueryHandler(self.selecionar_categoria, pattern="^categoria:")
        )

        # Não confirmar -> Escolher categoria
        self.app.add_handler(
            CallbackQueryHandler(
                self.escolher_categoria, pattern="^escolher_categoria$"
            )
        )

        self.app.add_handler(
            CallbackQueryHandler(self.criar_conta, pattern="^criar_conta$")
        )

        self.app.add_handler(
            CallbackQueryHandler(self.selecionar_tipo_conta, pattern="^tipo_conta:")
        )

        self.app.add_handler(
            CallbackQueryHandler(self.selecionar_conta, pattern="^conta:")
        )

    def iniciar(self):
        print("Pluto Telegram iniciado!")

        # Executa a verificação dos insights
        # periodicamente.
        self.app.job_queue.run_repeating(
            self._executar_scheduler,
            interval=60,
            first=10,
        )

        self.app.run_polling()


    def _criar_menu_principal(self):

        botoes = [
            [
                InlineKeyboardButton(
                    "🛒 Registrar compra",
                    callback_data="menu:compra"
                )
            ],
            [
                InlineKeyboardButton(
                    "💳 Minhas contas",
                    callback_data="menu:contas"
                ),
                InlineKeyboardButton(
                    "📋 Minhas compras",
                    callback_data="menu:compras"
                )
            ],
            [
                InlineKeyboardButton(
                    "📊 Dashboard",
                    callback_data="menu:dashboard"
                )
            ],
            [
                InlineKeyboardButton(
                    "💬 Falar com o Pluto",
                    callback_data="menu:conversa"
                )
            ],
            [
                InlineKeyboardButton(
                    "➕ Criar categoria",
                    callback_data="menu:categoria"
                ),
                InlineKeyboardButton(
                    "🏷️ Categorias",
                    callback_data="menu:categorias"
                )
            ],
            [
                InlineKeyboardButton(
                    "🧠 Insights",
                    callback_data="menu:insights"
                )
            ],
            [
                InlineKeyboardButton(
                    "❓ Ajuda",
                    callback_data="menu:help"
                )
            ]
        ]

        return InlineKeyboardMarkup(botoes)

    async def start(self, update, context):
        context.user_data.pop("planejamento_economia", None)
        context.user_data.pop("modo_conversa", None)
        context.user_data.pop("entrevista_financeira", None)
        await update.message.reply_text(
            "👋 *Olá! Eu sou o Pluto.* 🐶\n\n"
            "Seu assistente inteligente para organizar "
            "e entender seus gastos. 💰\n\n"
            "O que você deseja fazer?",
            parse_mode="Markdown",
            reply_markup=self._criar_menu_principal()
        )

    async def menu(self, update, context):
        context.user_data.pop("planejamento_economia", None)
        context.user_data.pop("modo_conversa", None)
        context.user_data.pop("entrevista_financeira", None)
        await update.message.reply_text(
            "🐶 *Menu principal*\n\n"
            "O que você deseja fazer?",
            parse_mode="Markdown",
            reply_markup=self._criar_menu_principal()
        )

    async def menu_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        try:
            await query.answer()
        except Exception as e:
            print(f"Callback expirado ou inválido: {e}")
            return

        acao = query.data.split(":", 1)[1]

        if acao == "principal":

            context.user_data.pop("planejamento_economia", None)
            context.user_data.pop("modo_conversa", None)
            context.user_data.pop("entrevista_financeira", None)

            await query.edit_message_text(
                "🐶 *Menu principal*\n\n"
                "O que você deseja fazer?",
                parse_mode="Markdown",
                reply_markup=self._criar_menu_principal()
            )

        elif acao == "compra":

            botoes = [
                [
                    InlineKeyboardButton(
                        "🐶 Menu principal",
                        callback_data="menu:principal"
                    )
                ]
            ]

            await query.edit_message_text(
                "🛒 *Registrar compra*\n\n"
                "Envie uma mensagem descrevendo sua compra.\n\n"
                "Exemplo:\n"
                "`Comprei um tênis por R$ 299,90`\n\n"
                "Você também pode enviar uma foto da compra 📷.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(botoes)
            )

        elif acao == "contas":

            await self.listar_contas(update, context)

        elif acao == "compras":

            await self.listar_compras(update, context)

        elif acao == "dashboard":

            usuario_id = update.effective_user.id

            link = gerar_link_login(usuario_id)

            teclado = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "📊 Abrir Dashboard",
                        url=link
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🐶 Menu principal",
                        callback_data="menu:principal"
                    )
                ]
            ])

            await query.edit_message_text(
                "Clique no botão abaixo para abrir seu dashboard.\n"
                "Por segurança, o link expira em 5 minutos.",
                reply_markup=teclado
            )

        elif acao == "categoria":

            await self.criar_categoria(update, context)

        elif acao == "categorias":

            await self.listar_categorias(update, context)

        elif acao == "conversa":

            await self._iniciar_conversa_financeira(update, context)

        elif acao == "insights":

            await self.insights(update, context)

        elif acao == "help":

            await self.help(update, context)

    async def abrir_dashboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        usuario_id = update.effective_user.id

        # Gera um link assinado e de curta duração. Quem abrir
        # esse link já entra logado como esse usuario_id, sem
        # precisar digitar senha nenhuma.
        link = gerar_link_login(usuario_id)

        botao = InlineKeyboardButton("📊 Abrir Dashboard", url=link)

        teclado = InlineKeyboardMarkup([[botao]])

        await update.message.reply_text(
            "Clique no botão abaixo para abrir seu dashboard.\n"
            "Por segurança, o link expira em 5 minutos.",
            reply_markup=teclado,
        )

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        mensagem = """
    *Como posso ajudar?* 🐶

    💰 *Registrar uma compra*

    Envie uma mensagem contando o que você comprou:

    `Comprei um tênis por R$ 299,90`

    Você também pode enviar uma *foto da compra* 📷.

    📊 *Acompanhar seus gastos*

    Acesse o dashboard para visualizar seu histórico e suas análises.

    🧠 *Analisar seus hábitos*

    Conforme você registra suas compras, o Pluto identifica padrões de consumo e gera insights.

    ⚙️ *Comandos*

    /start — Iniciar o Pluto
    /menu — Abrir o menu
    /help — Mostrar ajuda
    /compras — Listar compras
    /contas — Listar contas
    /categorias — Gerenciar categorias
    /dashboard — Abrir dashboard
    """

        botoes = [
            [
                InlineKeyboardButton(
                    "🐶 Menu principal",
                    callback_data="menu:principal"
                )
            ]
        ]

        teclado = InlineKeyboardMarkup(botoes)

        if update.callback_query:

            await update.callback_query.edit_message_text(
                mensagem,
                parse_mode="Markdown",
                reply_markup=teclado
            )

        else:

            await update.message.reply_text(
                mensagem,
                parse_mode="Markdown",
                reply_markup=teclado
            )

    async def receber_foto(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        mensagem = update.message.caption or ""
        usuario_id = update.effective_user.id

        # Encaminha a imagem para a IA
        service = CompraService(usuario_id, self.ia_service)

        await update.message.reply_text("Analisando sua compra...")

        foto = update.message.photo[-1]

        arquivo = await foto.get_file()

        caminho = "produto.jpg"

        await arquivo.download_to_drive(caminho)

        try:

            resultado = await asyncio.to_thread(
                service.processar_compra, imagem_path=caminho, mensagem=mensagem
            )

        except AnaliseIAError as e:

            print(f"Erro ao analisar imagem (IA): {e}")

            await update.message.reply_text(
                "Não consegui identificar essa compra pela imagem. "
                "Tente enviar outra foto ou descreva a compra por texto."
            )

            return

        except Exception as e:

            print(f"Erro ao analisar imagem: {e}")

            await update.message.reply_text(
                "Não consegui analisar a imagem agora. "
                "Tente novamente em alguns segundos."
            )

            return

        await self._enviar_confirmacao(update, context, resultado)

    async def _iniciar_conversa_financeira(self, update, context):
        context.user_data["modo_conversa"] = True
        perfil = context.user_data.get("perfil_financeiro")

        if perfil:
            texto = (
                "💬 *Conversa com o Pluto*\n\n"
                "Pode perguntar sobre orçamento, dívidas, economia ou investimentos."
            )
        else:
            context.user_data["entrevista_financeira"] = {
                "indice": 0,
                "respostas": [],
            }
            texto = (
                "💬 *Antes de começarmos, quero conhecer você um pouco.*\n\n"
                + self.PERGUNTAS_ENTREVISTA[0]
            )

        await update.callback_query.edit_message_text(
            texto,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🐶 Voltar ao menu", callback_data="menu:principal")
            ]]),
        )

    async def _continuar_entrevista_financeira(self, update, context, texto):
        entrevista = context.user_data["entrevista_financeira"]
        entrevista["respostas"].append(texto)
        entrevista["indice"] += 1

        if entrevista["indice"] < len(self.PERGUNTAS_ENTREVISTA):
            await update.message.reply_text(
                self.PERGUNTAS_ENTREVISTA[entrevista["indice"]]
            )
            return

        respostas = entrevista["respostas"]
        context.user_data["perfil_financeiro"] = {
            "objetivo": respostas[0],
            "situacao": respostas[1],
            "conhecimento_e_risco": respostas[2],
        }
        context.user_data.pop("entrevista_financeira", None)
        await update.message.reply_text(
            "Perfeito, já tenho uma base para adaptar nossa conversa. 🐶\n\n"
            "Agora me diga: sobre qual assunto financeiro você quer conversar?"
        )

    async def _responder_conversa_financeira(self, update, context, texto):
        usuario_id = update.effective_user.id
        historico = context.user_data.get("historico_assistente", [])

        try:
            if self.conversation_service is None:
                self.conversation_service = ConversationService()

            dados = await asyncio.to_thread(
                self.financial_context_service.obter, usuario_id
            )
            dados["perfil_declarado"] = context.user_data.get("perfil_financeiro", {})
            skills_conversa = tuple(
                skill for skill in self.skill_router.skills
                if skill.info.nome != "registrar_compra"
            )
            interpretacao = await asyncio.to_thread(
                self.conversation_service.interpretar,
                texto,
                skills_conversa,
                usuario_id,
                dados,
                historico,
            )
            resposta = interpretacao["resposta"] or (
                "Não consegui formular uma resposta. Tente perguntar de outra forma."
            )

            nome_skill = interpretacao["skill"]
            if nome_skill:
                skill = next(
                    (item for item in skills_conversa if item.info.nome == nome_skill),
                    None,
                )
                if skill is not None:
                    context.user_data.pop("modo_conversa", None)
                    await skill.executar(self, update, context)
                    return
        except Exception as erro:
            print(f"Erro na conversa financeira: {erro}")
            await update.message.reply_text(
                "Não consegui responder agora. Verifique a configuração da conversa "
                "e tente novamente em alguns instantes."
            )
            return

        await update.message.reply_text(resposta)
        historico.extend([
            {"role": "user", "content": texto},
            {"role": "assistant", "content": resposta},
        ])
        context.user_data["historico_assistente"] = historico[-12:]

    async def iniciar_planejamento_economia(self, update, context):
        context.user_data["planejamento_economia"] = True
        await update.message.reply_text(
            "Vamos montar seu plano mensal. 🐶\n\n"
            "Qual é o seu salário líquido, ou seja, o valor que realmente "
            "entra na sua conta por mês?\n\n"
            "Exemplo: `R$ 3.000,00`",
            parse_mode="Markdown",
        )

    async def _continuar_planejamento_economia(self, update, context, texto):
        try:
            salario = SavingsPlanService.interpretar_valor(texto)
            plano = SavingsPlanService.calcular(salario)
        except ValueError:
            await update.message.reply_text(
                "Não consegui entender o salário. Digite somente um valor maior "
                "que zero, por exemplo: `R$ 3.000,00`.",
                parse_mode="Markdown",
            )
            return

        context.user_data.pop("planejamento_economia", None)

        def moeda(valor):
            texto_valor = f"{valor:,.2f}"
            return "R$ " + texto_valor.replace(",", "X").replace(".", ",").replace("X", ".")

        await update.message.reply_text(
            "📊 *Seu plano mensal sugerido*\n\n"
            f"Salário líquido: *{moeda(plano['salario'])}*\n\n"
            f"🏠 *Necessidades — 50%:* {moeda(plano['necessidades'])}\n"
            "Moradia, alimentação, transporte e contas essenciais.\n\n"
            f"🎈 *Gastos flexíveis — 30%:* {moeda(plano['desejos'])}\n"
            "Lazer, assinaturas, compras e outros desejos.\n\n"
            f"🐷 *Guardar — 20%:* {moeda(plano['guardar'])}\n"
            "Priorize primeiro uma reserva de emergência.\n\n"
            "Essa é uma referência inicial. Se suas despesas essenciais já "
            "passam de 50%, podemos adaptar o plano à sua realidade.",
            parse_mode="Markdown",
        )

    async def receber_mensagem(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):

        texto = update.message.text.strip()

        if context.user_data.get("movimentacao_saldo"):
            await self._receber_valor_movimentacao_saldo(update, context, texto)
            return

        if context.user_data.get("editando_compra"):
            await self._receber_edicao_compra(update, context, texto)
            return
        if context.user_data.get("editando_conta"):
            await self._receber_edicao_conta(update, context, texto)
            return
        if context.user_data.get("editando_categoria"):
            await self._receber_edicao_categoria(update, context, texto)
            return

        if context.user_data.get("editando_horario_insights"):
            await self._receber_horario_insights(update, context, texto)
            return

        if context.user_data.get("planejamento_economia"):
            await self._continuar_planejamento_economia(update, context, texto)
            return

        skill_direta = self.skill_router.selecionar(texto)
        if skill_direta and skill_direta.info.nome == "planejar_economia":
            await skill_direta.executar(self, update, context)
            return

        if context.user_data.get("modo_conversa"):
            if "entrevista_financeira" in context.user_data:
                await self._continuar_entrevista_financeira(update, context, texto)
                return
            if skill_direta and skill_direta.info.nome != "registrar_compra":
                context.user_data.pop("modo_conversa", None)
                await skill_direta.executar(self, update, context)
                return
            await self._responder_conversa_financeira(update, context, texto)
            return

        # =====================================================
        # USUÁRIO ESTÁ CRIANDO UMA CONTA
        # =====================================================

        if context.user_data.get("criando_conta"):

            etapa = context.user_data.get("etapa_criacao_conta")

            usuario_id = update.effective_user.id

            service = CompraService(usuario_id, self.ia_service)

            # -------------------------------------------------
            # ETAPA 1 — NOME DA CONTA
            # -------------------------------------------------

            if etapa is None:

                if not texto:

                    await update.message.reply_text(
                        "❌ O nome da conta não pode ser vazio."
                    )

                    return

                context.user_data["nome_conta_pendente"] = texto

                context.user_data["etapa_criacao_conta"] = "tipo"

                botoes = [
                    [
                        InlineKeyboardButton(
                            "💳 Conta corrente",
                            callback_data="tipo_conta:CONTA_CORRENTE",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "💵 Carteira", callback_data="tipo_conta:CARTEIRA"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏦 Poupança", callback_data="tipo_conta:POUPANCA"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📈 Investimento", callback_data="tipo_conta:INVESTIMENTO"
                        )
                    ],
                ]

                await update.message.reply_text(
                    f"💳 Conta: *{texto}*\n\n" "Qual é o tipo da conta?",
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup(botoes),
                )

                return

            # -------------------------------------------------
            # ETAPA 2 — SALDO INICIAL
            # -------------------------------------------------

            if etapa == "saldo":

                texto_saldo = (
                    texto.replace("R$", "")
                    .replace(" ", "")
                    .replace(".", "")
                    .replace(",", ".")
                )

                try:

                    saldo = float(texto_saldo)

                except ValueError:

                    await update.message.reply_text(
                        "❌ Não consegui entender esse valor.\n\n"
                        "Digite, por exemplo:\n"
                        "`500` ou `R$ 500,00`",
                        parse_mode="Markdown",
                    )

                    return

                nome = context.user_data.get("nome_conta_pendente")

                tipo = context.user_data.get("tipo_conta_pendente")

                if not nome or not tipo:

                    await update.message.reply_text(
                        "❌ Os dados da conta foram perdidos. "
                        "Tente criar a conta novamente."
                    )

                    context.user_data.pop("criando_conta", None)

                    context.user_data.pop("etapa_criacao_conta", None)

                    return

                try:

                    service.adicionar_conta(nome=nome, tipo=tipo, saldo=saldo)

                    # Finaliza criação da conta
                    context.user_data.pop("criando_conta", None)

                    context.user_data.pop("etapa_criacao_conta", None)

                    context.user_data.pop("nome_conta_pendente", None)

                    context.user_data.pop("tipo_conta_pendente", None)

                    # Verifica se existe uma compra aguardando
                    compra = context.user_data.get("compra_pendente")

                    if compra is None:

                        await update.message.reply_text(
                            f"✅ Conta *{nome}* criada com sucesso!\n\n"
                            "Quando quiser continuar, use /menu.",
                            parse_mode="Markdown"
                        )

                        return

                    # Busca novamente as contas
                    contas = service.listar_contas()

                    botoes = []

                    for conta in contas:

                        botoes.append(
                            [
                                InlineKeyboardButton(
                                    f"{conta[1]}", callback_data=f"conta:{conta[0]}"
                                )
                            ]
                        )

                    await update.message.reply_text(
                        f"✅ Conta *{nome}* criada com sucesso!\n\n"
                        "💳 Em qual conta você pagou?",
                        parse_mode="Markdown",
                        reply_markup=InlineKeyboardMarkup(botoes),
                    )

                except Exception as e:

                    print(f"Erro ao criar conta: {e}")

                    await update.message.reply_text(
                        "❌ Não foi possível criar a conta.\n"
                        "Verifique se já existe uma conta com esse nome."
                    )

                return

        # =====================================================
        # USUÁRIO ESTÁ CRIANDO UMA CATEGORIA
        # =====================================================

        if context.user_data.get("criando_categoria"):

            nome_categoria = texto

            usuario_id = update.effective_user.id

            service = CompraService(usuario_id, self.ia_service)

            compra = context.user_data.get("compra_pendente")

            try:

                # Cria a categoria
                service.adicionar_categoria(nome_categoria)

                # Guarda a categoria para o momento
                # em que a conta for escolhida
                context.user_data["categoria_pendente"] = nome_categoria

                # Finaliza criação da categoria
                context.user_data.pop("criando_categoria", None)

                if compra is None:

                    await update.message.reply_text(
                        f"✅ Categoria '{nome_categoria}' criada."
                    )

                    return

                # Busca contas
                contas = service.listar_contas()

                if not contas:

                    botoes = [
                        [
                            InlineKeyboardButton(
                                "➕ Criar conta", callback_data="criar_conta"
                            )
                        ],
                        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
                    ]

                    await update.message.reply_text(
                        "💳 Você ainda não possui nenhuma conta cadastrada.\n\n"
                        "Crie uma conta para registrar esta compra.",
                        reply_markup=InlineKeyboardMarkup(botoes),
                    )

                    return

                botoes = []

                for conta in contas:

                    botoes.append(
                        [
                            InlineKeyboardButton(
                                f"💳 {conta[1]}", callback_data=f"conta:{conta[0]}"
                            )
                        ]
                    )

                botoes.append(
                    [
                        InlineKeyboardButton(
                            "➕ Criar outra conta", callback_data="criar_conta"
                        )
                    ]
                )

                await update.message.reply_text(
                    f"✅ Categoria '{nome_categoria}' criada.\n\n"
                    "💳 Em qual conta você pagou?",
                    reply_markup=InlineKeyboardMarkup(botoes),
                )

            except Exception as e:

                print(f"Erro ao criar categoria: {e}")

                await update.message.reply_text(
                    "❌ Não foi possível criar a categoria."
                )

            return

        # =====================================================
        # NOVA COMPRA
        # =====================================================

        skill = self.skill_router.selecionar(texto)
        if skill is not None and skill.info.nome != "registrar_compra":
            await skill.executar(self, update, context)
            return

        mensagem = texto

        usuario_id = update.effective_user.id

        service = CompraService(usuario_id, self.ia_service)

        await update.message.reply_text("Analisando sua compra...")

        try:

            resultado = await asyncio.to_thread(
                service.processar_compra, mensagem=mensagem
            )

        except AnaliseIAError as e:

            print(f"Erro ao analisar compra (IA): {e}")

            await update.message.reply_text(
                "Não consegui entender essa compra. "
                "Tente descrever novamente, incluindo o "
                "produto e o valor pago."
            )

            return

        except Exception as e:

            import traceback

            print(f"Erro ao analisar compra: {e}")
            traceback.print_exc()

            await update.message.reply_text(
                "Não consegui analisar a compra agora. "
                "Tente novamente em alguns segundos."
            )

            return

        await self._enviar_confirmacao(update, context, resultado)

    async def confirmar_compra(self, update, context):
        query = update.callback_query
        await query.answer()

        compra = context.user_data.get("compra_pendente")

        if compra is None:
            await query.edit_message_text("❌ Não encontrei uma compra pendente.")
            return

        usuario_id = update.effective_user.id
        service = CompraService(usuario_id, self.ia_service)

        contas = service.listar_contas()

        # Usuário ainda não possui contas
        if not contas:

            botoes = [
                [InlineKeyboardButton("➕ Criar conta", callback_data="criar_conta")],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar")],
            ]

            teclado = InlineKeyboardMarkup(botoes)

            await query.edit_message_text(
                "💳 Você ainda não possui nenhuma conta cadastrada.\n\n"
                "Para registrar esta compra, primeiro precisamos criar "
                "uma conta.\n\n"
                "Clique abaixo para começar:",
                reply_markup=teclado,
            )

            return

        # Usuário possui contas → escolher a conta
        botoes = []

        for conta in contas:
            botoes.append(
                [
                    InlineKeyboardButton(
                        f"💳 {conta[1]}", callback_data=f"conta:{conta[0]}"
                    )
                ]
            )

        botoes.append(
            [InlineKeyboardButton("➕ Criar outra conta", callback_data="criar_conta")]
        )

        teclado = InlineKeyboardMarkup(botoes)

        await query.edit_message_text(
            "💳 Em qual conta você realizou esta compra?", reply_markup=teclado
        )

    async def _enviar_confirmacao(self, update, context, resultado):
        """
        Exibe os dados identificados pela IA
        e aguarda a confirmação do usuário.
        """

        context.user_data["compra_pendente"] = resultado

        botoes = [
            [InlineKeyboardButton("✅ Confirmar", callback_data="confirmar")],
            [InlineKeyboardButton("❌ Não confirmar", callback_data="cancelar")],
        ]

        teclado = InlineKeyboardMarkup(botoes)

        await update.message.reply_text(
            f"Compra identificada:\n\n"
            f"🛍️ {resultado['produto']}\n"
            f"🏷️ {resultado['categoria']}\n"
            f"💰 R$ {resultado['valor']:.2f}\n\n"
            f"Deseja registrar essa compra?",
            reply_markup=teclado,
        )

    async def listar_compras(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        usuario_id = update.effective_user.id

        service = CompraService(usuario_id, self.ia_service)

        compras = service.listar_compras()

        if not compras:

            mensagem = "📭 Você ainda não possui compras registradas."

            botoes = [
                [
                    InlineKeyboardButton(
                        "🐶 Menu principal",
                        callback_data="menu:principal"
                    )
                ]
            ]

            teclado = InlineKeyboardMarkup(botoes)

            if update.callback_query:
                await update.callback_query.edit_message_text(
                    mensagem,
                    reply_markup=teclado
                )
            else:
                await update.message.reply_text(
                    mensagem,
                    reply_markup=teclado
                )

            return

        # Mostra somente as 3 compras mais recentes
        compras_recentes = compras[:3]

        mensagem = "🛍️ *Últimas compras*\n\n"

        mensagem += self._formatar_compras(compras_recentes)

        botoes = self._botoes_acoes_compras()

        # Se houver mais de 3 compras,
        # oferece a opção de visualizar o restante
        if len(compras) > 3:
            botoes.append(
                [
                    InlineKeyboardButton(
                        "📋 Ver mais deste mês", callback_data="compras:mais"
                    )
                ]
            )

        botoes.append(
            [
                InlineKeyboardButton(
                    "📅 Escolher período", callback_data="compras:periodo"
                )
            ]
        )

        teclado = InlineKeyboardMarkup(botoes)

        if update.callback_query:
            await update.callback_query.edit_message_text(
                mensagem,
                parse_mode="Markdown",
                reply_markup=teclado
            )
        else:
            await update.message.reply_text(
                mensagem,
                parse_mode="Markdown",
                reply_markup=teclado
            )

    def _formatar_compras(self, compras):

        mensagem = ""

        for compra in compras:

            id_compra = compra[0]
            produto = compra[1]
            categoria = compra[2]
            conta = compra[3]
            valor = compra[4]
            data = compra[5]

            # Caso o banco retorne datetime
            if isinstance(data, datetime):

                data_formatada = data

            else:

                data_formatada = datetime.strptime(str(data), "%Y-%m-%d %H:%M:%S")

            data_formatada = data_formatada.strftime("%d/%m/%Y às %H:%M")

            mensagem += (
                f"🧾 *{produto}*\n"
                f"🏷️ {categoria}\n"
                f"💰 R$ {valor:.2f}\n"
                f"💳 {conta}\n"
                f"📅 {data_formatada}\n\n"
            )

        return mensagem

    async def compras_callback(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        query = getattr(update, "callback_query", None)

        if query:
            await query.answer()

        acao = query.data.split(":", 1)[1]

        usuario_id = update.effective_user.id

        service = CompraService(usuario_id, self.ia_service)

        compras = service.listar_compras()

        if not compras:
            await query.edit_message_text(
                "📭 Você ainda não possui compras registradas."
            )

            return

        if acao == "editar":
            await self.editar_compras_lista(update, context)
            return

        if acao == "mais":
            agora = datetime.now()

            compras_mes = []

            for compra in compras:
                data = compra[5]

                if not isinstance(data, datetime):
                    data = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")


                if data.year == agora.year and data.month == agora.month:
                    compras_mes.append(compra)

            if not compras_mes:
                await query.edit_message_text(
                    "📭 Você não possui compras registradas neste mês."
                )

                return

            mensagem = "📋 *Compras deste mês*\n\n"

            mensagem += self._formatar_compras(compras_mes)

            botoes = self._botoes_acoes_compras()
            botoes.append([InlineKeyboardButton("📅 Escolher período", callback_data="compras:periodo")])

            teclado = InlineKeyboardMarkup(botoes)

            await query.edit_message_text(
                mensagem, parse_mode="Markdown", reply_markup=teclado
            )

        elif acao == "periodo":
            botoes = [
                [InlineKeyboardButton("📅 Este mês", callback_data="compras:este_mes")],
                [
                    InlineKeyboardButton(
                        "◀️ Mês passado", callback_data="compras:mes_passado"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 Últimos 3 meses", callback_data="compras:ultimos_3_meses"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗂️ Todas as compras", callback_data="compras:todas"
                    )
                ],
                [InlineKeyboardButton("🔙 Voltar", callback_data="compras:voltar")],
            ]

            teclado = InlineKeyboardMarkup(botoes)

            await query.edit_message_text(
                "📅 *Escolha um período:*", parse_mode="Markdown", reply_markup=teclado
            )

        elif acao in ("este_mes", "mes_passado", "ultimos_3_meses", "todas"):
            agora = datetime.now()

            compras_filtradas = []

            for compra in compras:

                data = compra[5]

                if not isinstance(data, datetime):
                    data = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")


                incluir = False

                if acao == "este_mes":
                    incluir = data.year == agora.year and data.month == agora.month

                    titulo = "📅 *Compras deste mês*"

                elif acao == "mes_passado":
                    if agora.month == 1:

                        mes = 12
                        ano = agora.year - 1

                    else:

                        mes = agora.month - 1
                        ano = agora.year

                    incluir = data.year == ano and data.month == mes

                    titulo = "◀️ *Compras do mês passado*"

                elif acao == "ultimos_3_meses":
                    limite = agora - timedelta(days=90)

                    incluir = data >= limite

                    titulo = "📊 *Compras dos últimos 3 meses*"

                elif acao == "todas":
                    incluir = True

                    titulo = "🗂️ *Todas as compras*"

                if incluir:
                    compras_filtradas.append(compra)

            if not compras_filtradas:
                mensagem = (
                    f"{titulo}\n\n" "📭 Nenhuma compra encontrada " "neste período."
                )

            else:
                mensagem = f"{titulo}\n\n" + self._formatar_compras(compras_filtradas)

            botoes = self._botoes_acoes_compras()
            botoes.append([InlineKeyboardButton("📅 Escolher período", callback_data="compras:periodo")])

            teclado = InlineKeyboardMarkup(botoes)

            await query.edit_message_text(
                mensagem, parse_mode="Markdown", reply_markup=teclado
            )

        elif acao == "voltar":
            compras_recentes = compras[:3]

            mensagem = "🛍️ *Últimas compras*\n\n" + self._formatar_compras(
                compras_recentes
            )

            botoes = []

            if len(compras) > 3:
                botoes.append(
                    [
                        InlineKeyboardButton(
                            "📋 Ver mais deste mês", callback_data="compras:mais"
                        )
                    ]
                )

            botoes.append(
                [
                    InlineKeyboardButton(
                        "📅 Escolher período", callback_data="compras:periodo"
                    )
                ]
            )

            teclado = InlineKeyboardMarkup(botoes)

            await query.edit_message_text(
                mensagem, parse_mode="Markdown", reply_markup=teclado
            )

    async def cancelar_compra(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        query = update.callback_query

        await query.answer()

        context.user_data.pop("compra_pendente", None)

        context.user_data.pop("categoria_pendente", None)

        context.user_data.pop("criando_categoria", None)

        await query.edit_message_text("Compra não registrada.")

    async def selecionar_categoria(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Define manualmente a categoria da compra
        e depois solicita a conta utilizada.
        """

        query = update.callback_query

        await query.answer()

        categoria = query.data.split(":", 1)[1]

        compra = context.user_data.get("compra_pendente")

        if compra is None:

            await query.edit_message_text("❌ Não encontrei a compra pendente.")

            return

        # Guarda a categoria escolhida
        context.user_data["categoria_pendente"] = categoria

        usuario_id = update.effective_user.id

        service = CompraService(usuario_id, self.ia_service)

        contas = service.listar_contas()

        if not contas:

            await query.edit_message_text(
                "💳 Você ainda não possui nenhuma conta cadastrada."
            )

            return

        botoes = []

        for conta in contas:

            conta_id = conta[0]
            nome = conta[1]

            botoes.append(
                [InlineKeyboardButton(f"💳 {nome}", callback_data=f"conta:{conta_id}")]
            )

        botoes.append(
            [InlineKeyboardButton("➕ Criar conta", callback_data="criar_conta")]
        )

        teclado = InlineKeyboardMarkup(botoes)

        await query.edit_message_text(
            f"🏷️ Categoria selecionada: {categoria}\n\n"
            f"💳 Em qual conta você pagou?",
            reply_markup=teclado,
        )

    async def escolher_categoria(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        await query.answer()

        usuario_id = update.effective_user.id

        # Busca as categorias do banco do usuário
        service = CompraService(usuario_id, self.ia_service)

        categorias = service.listar_categorias()

        botoes = []

        for categoria in categorias:

            botoes.append(
                [
                    InlineKeyboardButton(
                        categoria[1], callback_data=f"categoria:{categoria[1]}"
                    )
                ]
            )

        # Cadastro de nova categoria
        botoes.append(
            [
                InlineKeyboardButton(
                    "➕ Criar categoria", callback_data="criar_categoria"
                )
            ]
        )

        teclado = InlineKeyboardMarkup(botoes)

        await query.edit_message_text(
            "Escolha a categoria da compra:", reply_markup=teclado
        )

    async def selecionar_conta(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Registra a compra utilizando a conta escolhida
        pelo usuário.
        """

        query = update.callback_query

        await query.answer()

        compra = context.user_data.get("compra_pendente")

        if compra is None:

            await query.edit_message_text("❌ Não encontrei uma compra pendente.")

            return

        try:

            conta_id = int(query.data.split(":", 1)[1])

        except (ValueError, IndexError):

            await query.edit_message_text("❌ Conta inválida.")

            return

        usuario_id = update.effective_user.id

        service = CompraService(usuario_id, self.ia_service)

        try:

            # Verifica se a conta pertence ao usuário
            conta = service.buscar_conta(conta_id)

            if conta is None:

                await query.edit_message_text("❌ Conta não encontrada.")

                return

            if not conta[5]:

                await query.edit_message_text("❌ Essa conta está inativa.")

                return

            # Verifica se o usuário escolheu
            # uma categoria manualmente
            categoria_pendente = context.user_data.get("categoria_pendente")

            if categoria_pendente:

                service.confirmar_compra_com_categoria(
                    compra, categoria_pendente, conta_id
                )

            else:

                service.confirmar_compra(compra, conta_id)

            # Limpa os dados temporários
            context.user_data.pop("compra_pendente", None)

            context.user_data.pop("categoria_pendente", None)

            botoes = [
                [
                    InlineKeyboardButton(
                        "🐶 Menu principal",
                        callback_data="menu:principal"
                    )
                ]
            ]

            await query.edit_message_text(
                f"✅ Compra registrada com sucesso!\n\n"
                f"🛍️ {compra['produto']}\n"
                f"💰 R$ {compra['valor']:.2f}\n"
                f"💳 {conta[1]}",
                reply_markup=InlineKeyboardMarkup(botoes)
            )

        except Exception as e:

            print(f"Erro ao salvar compra: {e}")

            await query.edit_message_text("❌ Não foi possível registrar a compra.")

    def _botoes_acoes_compras(self):
        """Ações principais da tela de compras, sem poluir a lista."""
        return [
            [InlineKeyboardButton("✏️ Editar compra", callback_data="compras:editar")]
        ]

    async def editar_compras_lista(self, update, context):
        """Mostra as compras somente depois que o usuário escolhe editar."""
        query = update.callback_query
        await query.answer()

        service = CompraService(update.effective_user.id, self.ia_service)
        compras = service.listar_compras()

        if not compras:
            await query.edit_message_text(
                "📭 Você ainda não possui compras registradas.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Voltar", callback_data="menu:compras")]
                ])
            )
            return

        botoes = [
            [InlineKeyboardButton(
                f"🧾 {c[1]} · R$ {c[4]:.2f}",
                callback_data=f"editar_compra:{c[0]}"
            )]
            for c in compras
        ]
        botoes.append([InlineKeyboardButton("🔙 Voltar às compras", callback_data="menu:compras")])

        await query.edit_message_text(
            "✏️ *Editar compra*\n\nSelecione a compra que deseja alterar:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botoes)
        )

    async def compra_item(self, update, context):
        """Mostra os detalhes de uma compra e suas ações."""
        query = update.callback_query
        await query.answer()

        compra_id = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        compra = service.database.buscar_compra_detalhada(compra_id)

        if not compra:
            await query.edit_message_text("❌ Compra não encontrada.")
            return

        _, produto, _, categoria, _, conta, valor, data = compra
        if isinstance(data, datetime):
            data_formatada = data.strftime("%d/%m/%Y às %H:%M")
        else:
            data_formatada = str(data)

        botoes = [
            [InlineKeyboardButton("✏️ Alterar", callback_data=f"editar_compra:{compra_id}")],
            [InlineKeyboardButton("🗑️ Excluir", callback_data=f"excluir_compra:{compra_id}")],
            [InlineKeyboardButton("🔙 Voltar às compras", callback_data="menu:compras")],
        ]

        await query.edit_message_text(
            f"🧾 *Compra*\n\n"
            f"🛍️ {produto}\n"
            f"🏷️ {categoria}\n"
            f"💰 R$ {valor:.2f}\n"
            f"💳 {conta}\n"
            f"📅 {data_formatada}\n\n"
            "O que deseja fazer?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botoes),
        )

    async def editar_compra(self, update, context):
        query = update.callback_query
        await query.answer()
        compra_id = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        compra = service.database.buscar_compra_detalhada(compra_id)

        if not compra:
            await query.edit_message_text("❌ Compra não encontrada.")
            return

        _, produto, _, categoria, _, conta, valor, data = compra
        data_formatada = data.strftime("%d/%m/%Y às %H:%M") if isinstance(data, datetime) else str(data)

        botoes = [
            [InlineKeyboardButton("🛍️ Produto", callback_data=f"editar_compra_campo:{compra_id}:produto")],
            [InlineKeyboardButton("💰 Valor", callback_data=f"editar_compra_campo:{compra_id}:valor")],
            [InlineKeyboardButton("🏷️ Categoria", callback_data=f"editar_compra_campo:{compra_id}:categoria")],
            [InlineKeyboardButton("💳 Conta", callback_data=f"editar_compra_campo:{compra_id}:conta")],
            [InlineKeyboardButton("📅 Data e hora", callback_data=f"editar_compra_campo:{compra_id}:data")],
            [InlineKeyboardButton("🗑️ Excluir", callback_data=f"excluir_compra:{compra_id}")],
            [InlineKeyboardButton("🔙 Voltar", callback_data=f"compra_item:{compra_id}")],
        ]

        await query.edit_message_text(
            f"🧾 *Compra*\n\n"
            f"🛍️ {produto}\n🏷️ {categoria}\n💰 R$ {valor:.2f}\n"
            f"💳 {conta}\n📅 {data_formatada}\n\n"
            "Escolha o que deseja alterar:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botoes),
        )

    async def editar_compra_campo(self, update, context):
        query = update.callback_query
        await query.answer()
        _, cid, campo = query.data.split(":")
        cid = int(cid)
        service = CompraService(update.effective_user.id, self.ia_service)

        if campo == "categoria":
            botoes = [
                [InlineKeyboardButton(c[1], callback_data=f"editar_compra_categoria:{cid}:{c[0]}")]
                for c in service.listar_categorias()
            ]
            botoes.append([InlineKeyboardButton("🔙 Voltar", callback_data=f"editar_compra:{cid}")])
            await query.edit_message_text("🏷️ Escolha a nova categoria:", reply_markup=InlineKeyboardMarkup(botoes))
            return

        if campo == "conta":
            botoes = [
                [InlineKeyboardButton(f"💳 {c[1]}", callback_data=f"editar_compra_conta:{cid}:{c[0]}")]
                for c in service.listar_contas()
            ]
            botoes.append([InlineKeyboardButton("🔙 Voltar", callback_data=f"editar_compra:{cid}")])
            await query.edit_message_text("💳 Escolha a nova conta:", reply_markup=InlineKeyboardMarkup(botoes))
            return

        context.user_data["editando_compra"] = {"id": cid, "campo": campo}
        perguntas = {
            "produto": "🛍️ Digite o novo nome do produto:",
            "valor": "💰 Digite o novo valor (ex.: R$ 199,90):",
            "data": "📅 Digite a nova data e hora (DD/MM/AAAA HH:MM):",
        }
        await query.edit_message_text(perguntas[campo])

    async def _receber_edicao_compra(self, update, context, texto):
        ed = context.user_data["editando_compra"]
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            if ed["campo"] == "produto":
                service.database.atualizar_compra(ed["id"], produto=texto)
            elif ed["campo"] == "valor":
                valor_texto = texto.strip().upper().replace("R$", "").replace(" ", "")
                if not valor_texto:
                    raise ValueError("Digite um valor válido.")
                try:
                    if "," in valor_texto:
                        valor_texto = valor_texto.replace(".", "").replace(",", ".")
                    valor = Decimal(valor_texto)
                except InvalidOperation:
                    raise ValueError("Valor inválido. Use, por exemplo: 1000 ou R$ 1.000,50.")
                if valor < 0:
                    raise ValueError("O valor da compra não pode ser negativo.")
                service.database.atualizar_compra(ed["id"], valor=valor)
            else:
                service.database.atualizar_compra(
                    ed["id"], data_compra=datetime.strptime(texto, "%d/%m/%Y %H:%M")
                )

            compra_id = ed["id"]
            context.user_data.pop("editando_compra", None)
            await update.message.reply_text(
                "✅ Compra atualizada!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✏️ Continuar alterando", callback_data=f"editar_compra:{compra_id}")],
                    [InlineKeyboardButton("📋 Compras", callback_data="menu:compras")],
                ]),
            )
        except (ValueError, TypeError) as e:
            await update.message.reply_text(f"❌ {e}\n\nTente novamente.")

    async def editar_compra_categoria(self, update, context):
        query = update.callback_query
        await query.answer()
        _, cid, cat = query.data.split(":")
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.atualizar_compra(int(cid), categoria_id=int(cat))
            await self.editar_compra(update, context)
        except ValueError as e:
            await query.edit_message_text(f"❌ {e}")

    async def editar_compra_conta(self, update, context):
        query = update.callback_query
        await query.answer()
        _, cid, conta = query.data.split(":")
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.atualizar_compra(int(cid), conta_id=int(conta))
            await self.editar_compra(update, context)
        except ValueError as e:
            await query.edit_message_text(f"❌ {e}")

    async def excluir_compra(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        c = service.database.buscar_compra_detalhada(cid)
        if not c:
            await query.edit_message_text("❌ Compra não encontrada.")
            return
        await query.edit_message_text(
            f"⚠️ *Excluir {c[1]}?*\n\n"
            f"O valor de R$ {c[6]:.2f} será devolvido ao saldo.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑️ Sim, excluir", callback_data=f"confirmar_exclusao_compra:{cid}")],
                [InlineKeyboardButton("🔙 Cancelar", callback_data=f"compra_item:{cid}")],
            ]),
        )

    async def confirmar_exclusao_compra(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.excluir_compra(cid)
            await query.edit_message_text(
                "✅ Compra excluída e valor devolvido ao saldo.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📋 Compras", callback_data="menu:compras")]
                ]),
            )
        except ValueError as e:
            await query.edit_message_text(f"❌ {e}")

    async def conta_item(self, update, context):
        """Mostra os detalhes de uma conta e suas ações."""
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        c = service.buscar_conta(cid)

        if not c or not c[5]:
            await query.edit_message_text("❌ Conta não encontrada ou inativa.")
            return

        tipos = {
            "CONTA_CORRENTE": "💳 Conta corrente",
            "CARTEIRA": "💵 Carteira",
            "POUPANCA": "🏦 Poupança",
            "INVESTIMENTO": "📈 Investimento",
        }
        tipo = tipos.get(c[2], c[2])

        botoes = [
            [InlineKeyboardButton("➕ Adicionar dinheiro", callback_data=f"saldo_conta:adicionar:{cid}")],
            [InlineKeyboardButton("➖ Retirar dinheiro", callback_data=f"saldo_conta:retirar:{cid}")],
            [InlineKeyboardButton("🔄 Transferir", callback_data="saldo:transferir")],
            [InlineKeyboardButton("✏️ Alterar", callback_data=f"editar_conta:{cid}")],
            [InlineKeyboardButton("🗑️ Excluir", callback_data=f"excluir_conta:{cid}")],
            [InlineKeyboardButton("🔙 Voltar às contas", callback_data="menu:contas")],
        ]
        await query.edit_message_text(
            f"💳 *{c[1]}*\n\n"
            f"💰 Saldo: R$ {c[3]:.2f}\n"
            f"🏷️ Tipo: {tipo}\n\n"
            "O que deseja fazer?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botoes),
        )

    @staticmethod
    def _parse_valor_saldo(texto):
        """Converte valores como 1000, 1000,50 e R$ 1.000,50 em Decimal."""
        valor_texto = texto.strip().upper().replace("R$", "").replace(" ", "")
        if not valor_texto:
            raise ValueError("Digite um valor válido.")

        try:
            if "," in valor_texto:
                valor_texto = valor_texto.replace(".", "").replace(",", ".")
            valor = Decimal(valor_texto)
        except InvalidOperation:
            raise ValueError("Valor inválido. Use, por exemplo: 1000 ou R$ 1.000,50.")

        if valor <= 0:
            raise ValueError("O valor deve ser maior que zero.")

        return valor.quantize(Decimal("0.01"))

    async def iniciar_adicionar_saldo(self, update, context):
        query = update.callback_query
        await query.answer()
        await self._mostrar_contas_para_movimentacao(query, "adicionar")

    async def iniciar_retirar_saldo(self, update, context):
        query = update.callback_query
        await query.answer()
        await self._mostrar_contas_para_movimentacao(query, "retirar")

    async def _mostrar_contas_para_movimentacao(self, query, acao):
        service = CompraService(query.from_user.id, self.ia_service)
        contas = service.listar_contas()

        if not contas:
            await query.edit_message_text(
                "💳 Você ainda não possui nenhuma conta cadastrada.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Criar conta", callback_data="criar_conta")],
                    [InlineKeyboardButton("🔙 Voltar", callback_data="menu:contas")],
                ]),
            )
            return

        titulo = "➕ Adicionar dinheiro" if acao == "adicionar" else "➖ Retirar dinheiro"
        botoes = [
            [InlineKeyboardButton(
                f"💳 {conta[1]} · R$ {conta[3]:.2f}",
                callback_data=f"saldo_conta:{acao}:{conta[0]}"
            )]
            for conta in contas
        ]
        botoes.append([InlineKeyboardButton("🔙 Voltar às contas", callback_data="menu:contas")])

        await query.edit_message_text(
            f"{titulo}\n\nSelecione a conta:",
            reply_markup=InlineKeyboardMarkup(botoes),
        )

    async def iniciar_transferencia(self, update, context):
        query = update.callback_query
        await query.answer()
        service = CompraService(query.from_user.id, self.ia_service)
        contas = service.listar_contas()

        if len(contas) < 2:
            await query.edit_message_text(
                "🔄 *Transferir dinheiro*\n\n"
                "Você precisa ter pelo menos duas contas ativas para fazer uma transferência.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Criar conta", callback_data="criar_conta")],
                    [InlineKeyboardButton("🔙 Voltar às contas", callback_data="menu:contas")],
                ]),
            )
            return

        botoes = [
            [InlineKeyboardButton(
                f"💳 {conta[1]} · R$ {conta[3]:.2f}",
                callback_data=f"saldo_origem:{conta[0]}"
            )]
            for conta in contas
        ]
        botoes.append([InlineKeyboardButton("🔙 Voltar às contas", callback_data="menu:contas")])

        await query.edit_message_text(
            "🔄 *Transferir dinheiro*\n\nSelecione a conta de origem:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botoes),
        )

    async def selecionar_conta_movimentacao(self, update, context):
        query = update.callback_query
        await query.answer()
        _, acao, cid = query.data.split(":")
        cid = int(cid)
        service = CompraService(query.from_user.id, self.ia_service)
        conta = service.buscar_conta(cid)

        if not conta or not conta[5]:
            await query.edit_message_text("❌ Conta não encontrada ou inativa.")
            return

        context.user_data["movimentacao_saldo"] = {
            "acao": acao,
            "conta_id": cid,
            "conta_nome": conta[1],
        }

        texto = "adicionar" if acao == "adicionar" else "retirar"
        await query.edit_message_text(
            f"{'➕' if acao == 'adicionar' else '➖'} *{texto.capitalize()} dinheiro*\n\n"
            f"Conta: *{conta[1]}*\n\n"
            "Digite o valor:\n\n"
            "Exemplo: `500` ou `R$ 500,00`",
            parse_mode="Markdown",
        )

    async def selecionar_origem_transferencia(self, update, context):
        query = update.callback_query
        await query.answer()
        origem_id = int(query.data.split(":", 1)[1])
        service = CompraService(query.from_user.id, self.ia_service)
        origem = service.buscar_conta(origem_id)
        contas = service.listar_contas()

        if not origem or not origem[5]:
            await query.edit_message_text("❌ Conta de origem não encontrada ou inativa.")
            return

        botoes = [
            [InlineKeyboardButton(
                f"💳 {conta[1]} · R$ {conta[3]:.2f}",
                callback_data=f"saldo_destino:{origem_id}:{conta[0]}"
            )]
            for conta in contas if conta[0] != origem_id
        ]
        botoes.append([InlineKeyboardButton("🔙 Voltar", callback_data="saldo:transferir")])

        await query.edit_message_text(
            f"🔄 *Transferir dinheiro*\n\n"
            f"Origem: *{origem[1]}*\n\n"
            "Selecione a conta de destino:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botoes),
        )

    async def selecionar_destino_transferencia(self, update, context):
        query = update.callback_query
        await query.answer()
        _, origem_id, destino_id = query.data.split(":")
        origem_id = int(origem_id)
        destino_id = int(destino_id)
        service = CompraService(query.from_user.id, self.ia_service)
        origem = service.buscar_conta(origem_id)
        destino = service.buscar_conta(destino_id)

        if not origem or not origem[5] or not destino or not destino[5]:
            await query.edit_message_text("❌ Uma das contas não está disponível.")
            return

        context.user_data["movimentacao_saldo"] = {
            "acao": "transferir",
            "origem_id": origem_id,
            "destino_id": destino_id,
            "origem_nome": origem[1],
            "destino_nome": destino[1],
        }

        await query.edit_message_text(
            "🔄 *Transferir dinheiro*\n\n"
            f"De: *{origem[1]}*\n"
            f"Para: *{destino[1]}*\n\n"
            "Digite o valor da transferência:\n\n"
            "Exemplo: `500` ou `R$ 500,00`",
            parse_mode="Markdown",
        )

    async def _receber_valor_movimentacao_saldo(self, update, context, texto):
        dados = context.user_data.get("movimentacao_saldo")
        if not dados:
            return

        try:
            valor = self._parse_valor_saldo(texto)
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return

        dados["valor"] = str(valor)
        valor_formatado = f"R$ {valor:.2f}".replace(".", ",")

        if dados["acao"] == "transferir":
            mensagem = (
                "🔄 *Confirmar transferência?*\n\n"
                f"💳 De: *{dados['origem_nome']}*\n"
                f"💳 Para: *{dados['destino_nome']}*\n"
                f"💰 Valor: *{valor_formatado}*"
            )
            callback = f"confirmar_saldo:transferir:{dados['origem_id']}:{dados['destino_id']}:{valor}"
        else:
            simbolo = "adicionar" if dados["acao"] == "adicionar" else "retirar"
            emoji = "➕" if simbolo == "adicionar" else "➖"
            mensagem = (
                f"{emoji} *Confirmar movimentação?*\n\n"
                f"💳 Conta: *{dados['conta_nome']}*\n"
                f"💰 Valor: *{valor_formatado}*\n"
                f"Ação: *{'Adicionar' if simbolo == 'adicionar' else 'Retirar'} dinheiro*"
            )
            callback = f"confirmar_saldo:{dados['acao']}:{dados['conta_id']}:{valor}"

        await update.message.reply_text(
            mensagem,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirmar", callback_data=callback)],
                [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_saldo")],
            ]),
        )

    async def confirmar_movimentacao_saldo(self, update, context):
        query = update.callback_query
        await query.answer()
        partes = query.data.split(":")
        acao = partes[1]
        service = CompraService(query.from_user.id, self.ia_service)

        try:
            if acao == "transferir":
                origem_id = int(partes[2])
                destino_id = int(partes[3])
                valor = Decimal(partes[4])
                service.database.transferir_saldo(origem_id, destino_id, valor)
                mensagem = "✅ Transferência realizada com sucesso!"
            else:
                conta_id = int(partes[2])
                valor = Decimal(partes[3])
                if acao == "adicionar":
                    service.database.adicionar_saldo_conta(conta_id, valor)
                    mensagem = "✅ Dinheiro adicionado com sucesso!"
                elif acao == "retirar":
                    service.database.retirar_saldo_conta(conta_id, valor)
                    mensagem = "✅ Dinheiro retirado com sucesso!"
                else:
                    raise ValueError("Operação inválida.")

            context.user_data.pop("movimentacao_saldo", None)
            await query.edit_message_text(
                mensagem,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Ver contas", callback_data="menu:contas")],
                ]),
            )
        except (ValueError, InvalidOperation) as e:
            await query.edit_message_text(
                f"❌ {e}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Ver contas", callback_data="menu:contas")],
                ]),
            )

    async def cancelar_movimentacao_saldo(self, update, context):
        query = update.callback_query
        await query.answer()
        context.user_data.pop("movimentacao_saldo", None)
        await query.edit_message_text(
            "❌ Operação cancelada.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("💳 Minhas contas", callback_data="menu:contas")],
            ]),
        )

    async def editar_conta(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        c = service.buscar_conta(cid)
        if not c or not c[5]:
            await query.edit_message_text("❌ Conta não encontrada ou inativa.")
            return
        await query.edit_message_text(
            f"💳 *{c[1]}*\n💰 R$ {c[3]:.2f}\n\nO que deseja alterar?",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✏️ Nome", callback_data=f"editar_conta_nome:{cid}")],
                [InlineKeyboardButton("🏷️ Tipo", callback_data=f"editar_conta_tipo:{cid}")],
                [InlineKeyboardButton("🗑️ Excluir", callback_data=f"excluir_conta:{cid}")],
                [InlineKeyboardButton("🔙 Voltar", callback_data=f"conta_item:{cid}")],
            ]),
        )

    async def editar_conta_nome(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        context.user_data["editando_conta"] = {"id": cid}
        await query.edit_message_text("💳 Digite o novo nome da conta:")

    async def _receber_edicao_conta(self, update, context, texto):
        cid = context.user_data["editando_conta"]["id"]
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.atualizar_conta(cid, nome=texto)
            context.user_data.pop("editando_conta", None)
            await update.message.reply_text(
                "✅ Conta atualizada!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Minhas contas", callback_data="menu:contas")]
                ]),
            )
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")

    async def editar_conta_tipo(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        botoes = [
            [InlineKeyboardButton("💳 Conta corrente", callback_data=f"salvar_conta_tipo:{cid}:CONTA_CORRENTE")],
            [InlineKeyboardButton("💵 Carteira", callback_data=f"salvar_conta_tipo:{cid}:CARTEIRA")],
            [InlineKeyboardButton("🏦 Poupança", callback_data=f"salvar_conta_tipo:{cid}:POUPANCA")],
            [InlineKeyboardButton("📈 Investimento", callback_data=f"salvar_conta_tipo:{cid}:INVESTIMENTO")],
            [InlineKeyboardButton("🔙 Voltar", callback_data=f"editar_conta:{cid}")],
        ]
        await query.edit_message_text("🏷️ Escolha o novo tipo:", reply_markup=InlineKeyboardMarkup(botoes))

    async def salvar_conta_tipo(self, update, context):
        query = update.callback_query
        await query.answer()
        _, cid, tipo = query.data.split(":")
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.atualizar_conta(int(cid), tipo=tipo)
            await self.editar_conta(update, context)
        except ValueError as e:
            await query.edit_message_text(f"❌ {e}")

    async def excluir_conta(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        c = service.buscar_conta(cid)
        if not c or not c[5]:
            await query.edit_message_text("❌ Conta não encontrada ou já inativa.")
            return
        await query.edit_message_text(
            f"⚠️ *Excluir {c[1]}?*\n\n"
            "A conta será desativada e o histórico será preservado.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑️ Sim, excluir", callback_data=f"confirmar_exclusao_conta:{cid}")],
                [InlineKeyboardButton("🔙 Cancelar", callback_data=f"conta_item:{cid}")],
            ]),
        )

    async def confirmar_exclusao_conta(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.desativar_conta(cid)
            await query.edit_message_text(
                "✅ Conta excluída (desativada).",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💳 Contas", callback_data="menu:contas")]
                ]),
            )
        except ValueError as e:
            await query.edit_message_text(f"❌ {e}")

    async def categoria_item(self, update, context):
        """Mostra os detalhes de uma categoria e, quando permitido, suas ações."""
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        cat = service.database.buscar_categoria_por_id(cid)

        if not cat:
            await query.edit_message_text("❌ Categoria não encontrada.")
            return

        if cat[2] == "PERSONALIZADA":
            botoes = [
                [InlineKeyboardButton("✏️ Alterar", callback_data=f"editar_categoria:{cid}")],
                [InlineKeyboardButton("🗑️ Excluir", callback_data=f"excluir_categoria:{cid}")],
                [InlineKeyboardButton("🔙 Voltar às categorias", callback_data="menu:categorias")],
            ]
            descricao = "Categoria personalizada."
        else:
            botoes = [[InlineKeyboardButton("🔙 Voltar às categorias", callback_data="menu:categorias")]]
            descricao = "Categoria padrão do Pluto. Ela não pode ser alterada ou excluída."

        await query.edit_message_text(
            f"🏷️ *{cat[1]}*\n\n{descricao}\n\nO que deseja fazer?" if cat[2] == "PERSONALIZADA" else f"🏷️ *{cat[1]}*\n\n{descricao}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(botoes),
        )

    async def listar_categorias(self, update, context):
        service = CompraService(update.effective_user.id, self.ia_service)
        cats = service.listar_categorias()
        msg = "🏷️ *Categorias*\n\nSelecione uma categoria para ver os detalhes:"
        botoes = [
            [InlineKeyboardButton(
                f"{'🔒' if c[2] == 'PADRAO' else '🏷️'} {c[1]}",
                callback_data=f"categoria_item:{c[0]}"
            )]
            for c in cats
        ]
        botoes += [
            [InlineKeyboardButton("➕ Criar categoria", callback_data="criar_categoria")],
            [InlineKeyboardButton("🐶 Menu principal", callback_data="menu:principal")],
        ]
        teclado = InlineKeyboardMarkup(botoes)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(msg, parse_mode="Markdown", reply_markup=teclado)
        else:
            await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=teclado)

    async def _receber_edicao_categoria(self, update, context, texto):
        cid = context.user_data["editando_categoria"]["id"]
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.atualizar_categoria(cid, texto)
            context.user_data.pop("editando_categoria", None)
            await update.message.reply_text(
                "✅ Categoria atualizada!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏷️ Categorias", callback_data="menu:categorias")]
                ]),
            )
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")

    async def editar_categoria(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        cat = CompraService(update.effective_user.id, self.ia_service).database.buscar_categoria_por_id(cid)
        if not cat or cat[2] != "PERSONALIZADA":
            await query.edit_message_text("❌ Essa categoria não pode ser alterada.")
            return
        context.user_data["editando_categoria"] = {"id": cid}
        await query.edit_message_text(f"🏷️ Categoria atual: *{cat[1]}*\n\nDigite o novo nome:", parse_mode="Markdown")

    async def excluir_categoria(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        cat = CompraService(update.effective_user.id, self.ia_service).database.buscar_categoria_por_id(cid)
        if not cat or cat[2] != "PERSONALIZADA":
            await query.edit_message_text("❌ Essa categoria não pode ser excluída.")
            return
        await query.edit_message_text(
            f"⚠️ *Excluir {cat[1]}?*\n\n"
            "Se estiver sendo usada por compras, a exclusão será bloqueada para preservar o histórico.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🗑️ Sim, excluir", callback_data=f"confirmar_exclusao_categoria:{cid}")],
                [InlineKeyboardButton("🔙 Cancelar", callback_data=f"categoria_item:{cid}")],
            ]),
        )

    async def confirmar_exclusao_categoria(self, update, context):
        query = update.callback_query
        await query.answer()
        cid = int(query.data.split(":", 1)[1])
        service = CompraService(update.effective_user.id, self.ia_service)
        try:
            service.database.excluir_categoria(cid)
            await query.edit_message_text(
                "✅ Categoria excluída.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏷️ Categorias", callback_data="menu:categorias")]
                ]),
            )
        except ValueError as e:
            await query.edit_message_text(
                f"❌ {e}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏷️ Categorias", callback_data="menu:categorias")]
                ]),
            )

    async def criar_conta(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Inicia o processo de criação de uma nova conta.
        """

        query = update.callback_query

        if query:
            await query.answer()

        context.user_data["criando_conta"] = True
        context.user_data["etapa_criacao_conta"] = None

        context.user_data.pop("nome_conta_pendente", None)

        context.user_data.pop("tipo_conta_pendente", None)

        mensagem = (
            "💳 Vamos criar uma nova conta.\n\n"
            "Digite o nome da conta:\n\n"
            "Exemplo: Nubank"
        )
        if query:
            await query.edit_message_text(mensagem)
        else:
            await update.message.reply_text(mensagem)

    async def selecionar_tipo_conta(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Define o tipo da conta durante o processo
        de criação de uma nova conta.
        """

        query = update.callback_query

        await query.answer()

        tipo = query.data.split(":", 1)[1]

        tipos = {
            "CONTA_CORRENTE": "💳 Conta corrente",
            "CARTEIRA": "💵 Carteira",
            "POUPANCA": "🏦 Poupança",
            "INVESTIMENTO": "📈 Investimento",
        }

        nome_tipo = tipos.get(tipo)

        if nome_tipo is None:
            await query.edit_message_text("❌ Tipo de conta inválido.")
            return

        # Guarda o tipo escolhido
        context.user_data["tipo_conta_pendente"] = tipo

        # Avança para a próxima etapa
        context.user_data["etapa_criacao_conta"] = "saldo"

        nome = context.user_data.get("nome_conta_pendente")

        if not nome:
            await query.edit_message_text(
                "❌ O nome da conta não foi encontrado.\n"
                "Tente criar a conta novamente."
            )

            context.user_data.pop("criando_conta", None)

            return

        await query.edit_message_text(
            f"💳 Conta: *{nome}*\n"
            f"🏷️ Tipo: {nome_tipo}\n\n"
            "💰 Qual é o saldo inicial?\n\n"
            "Exemplo:\n"
            "`500`\n"
            "ou\n"
            "`R$ 500,00`",
            parse_mode="Markdown",
        )

    async def criar_categoria(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Inicia o processo de criação de uma nova categoria.
        """

        query = getattr(update, "callback_query", None)

        if query:
            await query.answer()

        context.user_data["criando_categoria"] = True

        mensagem = (
            "🏷️ Vamos criar uma nova categoria.\n\n"
            "Digite o nome da categoria:\n\n"
            "Exemplo: Alimentação"
        )
        if query:
            await query.edit_message_text(mensagem)
        else:
            await update.message.reply_text(mensagem)

    async def listar_contas(self, update, context):
        usuario_id = update.effective_user.id
        service = CompraService(usuario_id, self.ia_service)
        contas = service.listar_contas()

        if not contas:
            mensagem = (
                "💳 *Suas contas*\n\n"
                "Você ainda não possui nenhuma conta cadastrada."
            )
            botoes = [
                [InlineKeyboardButton("➕ Criar conta", callback_data="criar_conta")],
                [InlineKeyboardButton("🐶 Menu principal", callback_data="menu:principal")],
            ]
        else:
            mensagem = "💳 *Suas contas*\n\nSelecione uma conta para ver os detalhes:"
            botoes = [
                [InlineKeyboardButton(
                    f"💳 {conta[1]} · R$ {conta[3]:.2f}",
                    callback_data=f"conta_item:{conta[0]}"
                )]
                for conta in contas
            ]
            botoes += [
                [InlineKeyboardButton("➕ Adicionar dinheiro", callback_data="saldo:adicionar")],
                [InlineKeyboardButton("➖ Retirar dinheiro", callback_data="saldo:retirar")],
                [InlineKeyboardButton("🔄 Transferir", callback_data="saldo:transferir")],
                [InlineKeyboardButton("➕ Criar conta", callback_data="criar_conta")],
                [InlineKeyboardButton("🐶 Menu principal", callback_data="menu:principal")],
            ]

        teclado = InlineKeyboardMarkup(botoes)
        if update.callback_query:
            await update.callback_query.answer()
            await update.callback_query.edit_message_text(
                mensagem, parse_mode="Markdown", reply_markup=teclado
            )
        else:
            await update.message.reply_text(
                mensagem, parse_mode="Markdown", reply_markup=teclado
            )

    @staticmethod
    def _nome_frequencia(frequencia):
        return {
            "DIARIO": "Diário",
            "SEMANAL": "Semanal",
            "NENHUM": "Desativado",
        }.get(frequencia, frequencia.title())

    @staticmethod
    def _formatar_horario(horario):
        if horario is None:
            return "09:00"
        return horario.strftime("%H:%M") if hasattr(horario, "strftime") else str(horario)[:5]

    def _teclado_insights(self, configuracao):
        ativo = configuracao["ativo"]
        frequencia = configuracao["frequencia"]
        horario = self._formatar_horario(configuracao["horario"])

        status = "🔔 Ativadas" if ativo else "🔕 Desativadas"
        resumo = f"{status}\n📅 Frequência: {self._nome_frequencia(frequencia)}"
        if ativo:
            resumo += f"\n⏰ Horário: {horario}"

        botoes = [
            [InlineKeyboardButton("📊 Ver insight agora", callback_data="insights:manual")],
            [InlineKeyboardButton("⚙️ Configurar notificações", callback_data="insights:config")],
            [InlineKeyboardButton("🐶 Menu principal", callback_data="menu:principal")],
        ]
        return resumo, InlineKeyboardMarkup(botoes)

    async def insights(self, update, context):
        usuario_id = update.effective_user.id
        configuracao = Database(usuario_id).buscar_configuracao_insights()
        mensagem_status, teclado = self._teclado_insights(configuracao)
        mensagem = (
            "🧠 *Insights do Pluto*\n\n"
            "O Pluto analisa seus gastos e pode enviar insights "
            "automaticamente.\n\n"
            f"{mensagem_status}"
        )

        if update.callback_query:
            await update.callback_query.edit_message_text(
                mensagem, parse_mode="Markdown", reply_markup=teclado
            )
        else:
            await update.message.reply_text(
                mensagem, parse_mode="Markdown", reply_markup=teclado
            )

    async def _mostrar_config_insights(self, update, context):
        query = update.callback_query
        usuario_id = update.effective_user.id
        configuracao = Database(usuario_id).buscar_configuracao_insights()

        ativo = configuracao["ativo"]
        frequencia = configuracao["frequencia"]
        horario = self._formatar_horario(configuracao["horario"])

        mensagem = (
            "⚙️ *Configurar notificações*\n\n"
            f"🔔 Notificações: {'Ativadas' if ativo else 'Desativadas'}\n"
            f"📅 Frequência: {self._nome_frequencia(frequencia)}\n"
            f"⏰ Horário: {horario}\n\n"
            "Escolha o que deseja alterar:"
        )

        botoes = [
            [InlineKeyboardButton("🔔 Ativar" if not ativo else "🔕 Desativar", callback_data="insights:toggle")],
            [InlineKeyboardButton("☀️ Diário", callback_data="insights:freq:DIARIO"),
             InlineKeyboardButton("📆 Semanal", callback_data="insights:freq:SEMANAL")],
            [InlineKeyboardButton("⏰ Alterar horário", callback_data="insights:horario")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="insights:menu")],
        ]

        await query.edit_message_text(
            mensagem, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(botoes)
        )

    async def insights_callback(self, update, context):
        query = update.callback_query
        await query.answer()
        partes = query.data.split(":")
        acao = partes[1]
        usuario_id = update.effective_user.id
        database = Database(usuario_id)

        if acao == "menu":
            await self.insights(update, context)
            return

        if acao == "config":
            await self._mostrar_config_insights(update, context)
            return

        if acao == "toggle":
            config = database.buscar_configuracao_insights()
            novo_estado = not config["ativo"]
            database.definir_insights_ativos(novo_estado)
            if novo_estado and config["frequencia"] == "NENHUM":
                database.atualizar_frequencia_insights("SEMANAL")
            await self._mostrar_config_insights(update, context)
            return

        if acao == "freq" and len(partes) == 3:
            frequencia = partes[2]
            database.atualizar_frequencia_insights(frequencia)
            await self._mostrar_config_insights(update, context)
            return

        if acao == "horario":
            context.user_data["editando_horario_insights"] = True
            await query.edit_message_text(
                "⏰ *Alterar horário*\n\n"
                "Digite o horário em que deseja receber seus insights.\n\n"
                "Exemplo: `14:30`\n\n"
                "Use o formato *HH:MM*.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("❌ Cancelar", callback_data="insights:config")]
                ]),
            )
            return

        if acao == "manual":
            try:
                from src.services.insight_service import InsightService
                service = InsightService(database)
                periodo = "diario"
                dados = service.gerar_dados_insight(periodo)
                mensagem = self.scheduler_service.groq_service.gerar_insight(dados)
                await query.edit_message_text(
                    "🐶 *Insight do Pluto* 🧠\n\n" + mensagem,
                    parse_mode="Markdown",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🧠 Insights", callback_data="insights:menu")]
                    ]),
                )
            except Exception as erro:
                print(f"Erro ao gerar insight manual: {erro}")
                await query.edit_message_text(
                    "Não consegui gerar um insight agora. Tente novamente em alguns instantes.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Voltar", callback_data="insights:menu")]
                    ]),
                )
            return

    async def _receber_horario_insights(self, update, context, texto):
        try:
            horario = datetime.strptime(texto.strip(), "%H:%M").strftime("%H:%M")
        except ValueError:
            await update.message.reply_text(
                "❌ Horário inválido.\n\nDigite no formato `HH:MM`, por exemplo `14:30`.",
                parse_mode="Markdown",
            )
            return

        usuario_id = update.effective_user.id
        database = Database(usuario_id)
        database.atualizar_horario_insights(horario)
        context.user_data.pop("editando_horario_insights", None)

        configuracao = database.buscar_configuracao_insights()
        mensagem_status, teclado = self._teclado_insights(configuracao)
        await update.message.reply_text(
            "✅ *Horário atualizado!*\n\n"
            f"{mensagem_status}",
            parse_mode="Markdown",
            reply_markup=teclado,
        )

    async def _enviar_insight(self, telegram_id, mensagem):
        """
        Envia um insight automático para um usuário do Telegram.
        """

        await self.app.bot.send_message(
            chat_id=telegram_id,
            text=(
                "🐶 *Insight do Pluto* 🧠\n\n"
                f"{mensagem}"
            ),
            parse_mode="Markdown",
        )

    async def _executar_scheduler(
        self,
        context: ContextTypes.DEFAULT_TYPE
    ):
        """
        Executa a verificação dos insights automáticos.
        """

        print("[SCHEDULER] Verificando insights...")

        try:

            resultados = await self.scheduler_service.processar_insights(
                self._enviar_insight
            )

            if resultados:

                print(
                    f"[SCHEDULER] {len(resultados)} "
                    "usuário(s) processado(s)."
                )

            else:

                print(
                    "[SCHEDULER] Nenhum usuário precisa "
                    "receber insight agora."
                )

        except Exception as erro:

            print(
                f"[SCHEDULER] Erro geral: {erro}"
            )
