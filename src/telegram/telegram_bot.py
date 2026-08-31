import os

from dotenv import load_dotenv

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

from src.services.gemini_service import GeminiService
from src.services.compra_service import CompraService
from src.services.exceptions import AnaliseIAError
from src.services.auth_service import gerar_link_login

from datetime import datetime, timedelta

class TelegramBot:

    def __init__(self):

        load_dotenv()

        self.token = os.environ["TELEGRAM_BOT_TOKEN"]

        # Serviço do Gemini para análise de imagens
        self.gemini_service = GeminiService()

        # Aplicação do Telegram
        self.app = (
            Application
            .builder()
            .token(self.token)
            .build()
        )

        # Registra todos os comandos
        self._configurar_handlers()

    def _configurar_handlers(self):

        # Comando para iniciar o bot
        self.app.add_handler(
            CommandHandler(
                "start",
                self.start
            )
        )

        # Envia o link de acesso ao dashboard web
        self.app.add_handler(
            CommandHandler(
                "dashboard",
                self.abrir_dashboard
            )
        )

        # Comando de ajuda
        self.app.add_handler(
            CommandHandler(
                "help",
                self.help
            )
        )

        # Recebe fotos do usuário
        self.app.add_handler(
            MessageHandler(
                filters.PHOTO,
                self.receber_foto
            )
        )

        # Receve mensagens de texto
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.receber_mensagem
            )
        )

        # Confirma a compra
        self.app.add_handler(
            CallbackQueryHandler(
                self.confirmar_compra,
                pattern="^confirmar$"
            )
        )

        # Lista as compras do usuário
        self.app.add_handler(
            CommandHandler(
                "compras",
                self.listar_compras
            )
        )

        self.app.add_handler(
            CallbackQueryHandler(
                self.compras_callback,
                pattern="^compras:"
            )
        )

        # Cancela a compra
        self.app.add_handler(
            CallbackQueryHandler(
                self.cancelar_compra,
                pattern="^cancelar$"
            )
        )
        
        # Cria categoria
        self.app.add_handler(
            CallbackQueryHandler(
                self.criar_categoria,
                pattern="^criar_categoria$"
            )
        )
        
        # Seleciona categoria
        self.app.add_handler(
            CallbackQueryHandler(
                self.selecionar_categoria,
                pattern="^categoria:"
            )
        )

        # Não confirmar -> Escolher categoria
        self.app.add_handler(
            CallbackQueryHandler(
                self.escolher_categoria,
                pattern="^escolher_categoria$"
            )
        )
        
    def iniciar(self):
        print(
            "Pluto Telegram iniciado!"
        )

        self.app.run_polling()

    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        await update.message.reply_text(
            """
*Olá! Eu sou o Pluto.* 🐶

Seu assistente inteligente para organizar e entender seus gastos. 💰

Para começar, é só me contar o que você comprou:

`Comprei uma camisa de corrida por R$ 129,90`

Você também pode *enviar uma foto da sua compra.* 📷
Eu identifico as informações e peço sua confirmação antes de registrar.

📊 *Quer acompanhar seus gastos de forma visual?*
Use /dashboard para abrir seu painel.

❓ *Precisa de ajuda?*
Use /help para ver tudo o que posso fazer.
""",
            parse_mode="Markdown"
        )

    async def abrir_dashboard(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        usuario_id = update.effective_user.id

        # Gera um link assinado e de curta duração. Quem abrir
        # esse link já entra logado como esse usuario_id, sem
        # precisar digitar senha nenhuma.
        link = gerar_link_login(usuario_id)

        botao = InlineKeyboardButton(
            "📊 Abrir Dashboard",
            url=link
        )

        teclado = InlineKeyboardMarkup([[botao]])

        await update.message.reply_text(
            "Clique no botão abaixo para abrir seu dashboard.\n"
            "Por segurança, o link expira em 5 minutos.",
            reply_markup=teclado
        )

    async def help(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        await update.message.reply_text(
        """
        *Como posso ajudar?* 🐶

        💰 *Registrar uma compra*

        Envie uma mensagem contando o que você comprou:

        `Comprei um tênis por R$ 299,90`

        Você também pode enviar uma *foto da compra* 📷 e eu tentarei identificar o produto, categoria e valor.

        🔎 *Confirmar uma compra*

        Antes de registrar, eu mostro os dados que identifiquei para você confirmar ou escolher outra categoria.

        📊 *Acompanhar seus gastos*

        Use /dashboard para abrir seu painel e visualizar seu histórico e suas análises.

        🧠 *Analisar seus hábitos*

        Conforme você registra suas compras, o Pluto identifica padrões de consumo e gera insights sobre seus gastos.

        🔮 *Recomendações*

        O Pluto pode identificar possíveis compras recorrentes e enviar recomendações personalizadas com base nos seus hábitos.

        ⚙️ *Comandos disponíveis*

        /start — Iniciar o Pluto
        /help — Mostrar esta ajuda
        /dashboard — Abrir seu dashboard
            """,
            parse_mode="Markdown"
        )

    async def receber_foto(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        mensagem = update.message.caption or ""
        usuario_id = update.effective_user.id

        # Encaminha a imagem para o Gemini
        service = CompraService(
            usuario_id,
            self.gemini_service
        )

        await update.message.reply_text(
            "Analisando sua compra..."
        )

        foto = update.message.photo[-1]

        arquivo = await foto.get_file()

        caminho = "produto.jpg"

        await arquivo.download_to_drive(
            caminho
        )

        try:

            resultado = service.processar_compra(
                imagem_path=caminho,
                mensagem=mensagem
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

        await self._enviar_confirmacao(
            update,
            context,
            resultado
        )

    async def receber_mensagem(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        # Usuário está criando uma categoria
        if context.user_data.get("criando_categoria"):

            nome_categoria = update.message.text.strip()

            usuario_id = update.effective_user.id

            service = CompraService(
                usuario_id,
                self.gemini_service
            )

            compra = context.user_data.get(
                "compra_pendente"
            )

            try:

                # Cria a categoria
                service.adicionar_categoria(
                    nome_categoria
                )

                # Salva a compra usando a nova categoria
                if compra:

                    service.confirmar_compra_com_categoria(
                        compra,
                        nome_categoria
                    )

                # Limpa os dados
                context.user_data.pop(
                    "criando_categoria",
                    None
                )

                context.user_data.pop(
                    "compra_pendente",
                    None
                )

                await update.message.reply_text(
                    f"Categoria '{nome_categoria}' criada.\n\n"
                    f"Compra registrada com sucesso"
                )

            except Exception as e:

                print(
                    f"Erro ao criar categoria/salvar compra: {e}"
                )

                await update.message.reply_text(
                    "Não foi possível criar a categoria "
                    "ou salvar a compra."
                )

            return

        mensagem = update.message.text
        usuario_id = update.effective_user.id

        # Decide qual serviço de IA utilizar
        service = CompraService(
            usuario_id,
            self.gemini_service
        )

        await update.message.reply_text(
            "Analisando sua compra..."
        )

        try:

            resultado = service.processar_compra(
                mensagem=mensagem
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

            print(f"Erro ao analisar compra: {e}")

            await update.message.reply_text(
                "Não consegui analisar a compra agora. "
                "Tente novamente em alguns segundos."
            )

            return

        await self._enviar_confirmacao(
            update,
            context,
            resultado
        )

    async def confirmar_compra(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        await query.answer()

        compra = context.user_data.get(
            "compra_pendente"
        )

        if compra is None:

            await query.edit_message_text(
                "Não encontrei uma compra pendente."
            )

            return

        usuario_id = update.effective_user.id

        service = CompraService(
            usuario_id,
            self.gemini_service
        )

        try:

            # Salva a compra
            service.confirmar_compra(
                compra
            )

            context.user_data.pop(
                "compra_pendente",
                None
            )

            await query.edit_message_text(
                "✅ Compra registrada com sucesso!"
            )

        except Exception as e:

            print(
                f"Erro ao salvar compra: {e}"
            )

            await query.edit_message_text(
                "Erro ao salvar a compra."
            )

    async def _enviar_confirmacao(
        self,
        update,
        context,
        resultado
    ):

        # Guarda temporariamente a compra na memória até o usuário escolher o que fazer
        context.user_data[
            "compra_pendente"
        ] = resultado

        botoes = [
            [
                InlineKeyboardButton(
                    "✅ Confirmar",
                    callback_data="confirmar"
                ),
                InlineKeyboardButton(
                    "❌ Não confirmar",
                    callback_data="escolher_categoria"
                )
            ]
        ]

        teclado = InlineKeyboardMarkup(
            botoes
        )

        await update.message.reply_text(
            f"Compra identificada:\n\n"
            f"Produto: {resultado['produto']}\n"
            f"Categoria: {resultado['categoria']}\n"
            f"Valor: R$ {resultado['valor']:.2f}\n\n"
            f"Deseja registrar essa compra?",
            reply_markup=teclado
        )

    async def listar_compras(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        usuario_id = update.effective_user.id

        service = CompraService(
            usuario_id,
            self.gemini_service
        )

        compras = service.listar_compras()

        if not compras:
            await update.message.reply_text(
                "📭 Você ainda não possui compras registradas."
            )

            return

        # Mostra somente as 3 compras mais recentes
        compras_recentes = compras[:3]

        mensagem = "🛍️ *Últimas compras*\n\n"

        mensagem += self._formatar_compras(
            compras_recentes
        )

        botoes = []

        # Se houver mais de 3 compras,
        # oferece a opção de visualizar o restante
        if len(compras) > 3:
            botoes.append([
                InlineKeyboardButton(
                    "📋 Ver mais deste mês",
                    callback_data="compras:mais"
                )
            ])

        botoes.append([
            InlineKeyboardButton(
                "📅 Escolher período",
                callback_data="compras:periodo"
            )
        ])

        teclado = InlineKeyboardMarkup(
            botoes
        )

        await update.message.reply_text(
            mensagem,
            parse_mode="Markdown",
            reply_markup=teclado
        )

    def _formatar_compras(
        self,
        compras
    ):

        mensagem = ""

        for compra in compras:
            id_compra = compra[0]
            produto = compra[1]
            categoria = compra[2]
            valor = compra[3]
            data = compra[4]

            data = datetime.strptime(
                data,
                "%Y-%m-%d %H:%M:%S"
            )

            # Ajuste para horário de Brasília
            data = data - timedelta(hours=3)

            data_formatada = data.strftime(
                "%d/%m/%Y às %H:%M"
            )

            mensagem += (
                f"🧾 *{produto}*\n"
                f"🏷️ {categoria}\n"
                f"💰 R$ {valor:.2f}\n"
                f"📅 {data_formatada}\n\n"
            )

        return mensagem

    async def compras_callback(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):
        query = update.callback_query

        await query.answer()

        acao = query.data.split(
            ":",
            1
        )[1]

        usuario_id = update.effective_user.id

        service = CompraService(
            usuario_id,
            self.gemini_service
        )

        compras = service.listar_compras()

        if not compras:
            await query.edit_message_text(
                "📭 Você ainda não possui compras registradas."
            )

            return

        if acao == "mais":
            agora = datetime.now()

            compras_mes = []

            for compra in compras:
                data = datetime.strptime(
                    compra[4],
                    "%Y-%m-%d %H:%M:%S"
                )

                # Mesmo ajuste utilizado na listagem
                data = data - timedelta(hours=3)

                if (
                    data.year == agora.year
                    and data.month == agora.month
                ):
                    compras_mes.append(compra)

            if not compras_mes:
                await query.edit_message_text(
                    "📭 Você não possui compras registradas neste mês."
                )

                return

            mensagem = "📋 *Compras deste mês*\n\n"

            mensagem += self._formatar_compras(
                compras_mes
            )

            botoes = [
                [
                    InlineKeyboardButton(
                        "📅 Escolher período",
                        callback_data="compras:periodo"
                    )
                ]
            ]

            teclado = InlineKeyboardMarkup(
                botoes
            )

            await query.edit_message_text(
                mensagem,
                parse_mode="Markdown",
                reply_markup=teclado
            )

        elif acao == "periodo":
            botoes = [
                [
                    InlineKeyboardButton(
                        "📅 Este mês",
                        callback_data="compras:este_mes"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "◀️ Mês passado",
                        callback_data="compras:mes_passado"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "📊 Últimos 3 meses",
                        callback_data="compras:ultimos_3_meses"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🗂️ Todas as compras",
                        callback_data="compras:todas"
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 Voltar",
                        callback_data="compras:voltar"
                    )
                ]
            ]

            teclado = InlineKeyboardMarkup(
                botoes
            )

            await query.edit_message_text(
                "📅 *Escolha um período:*",
                parse_mode="Markdown",
                reply_markup=teclado
            )
        
        elif acao in (
            "este_mes",
            "mes_passado",
            "ultimos_3_meses",
            "todas"
        ):
            agora = datetime.now()

            compras_filtradas = []

            for compra in compras:
                data = datetime.strptime(
                    compra[4],
                    "%Y-%m-%d %H:%M:%S"
                )

                data = data - timedelta(hours=3)

                incluir = False

                if acao == "este_mes":
                    incluir = (
                        data.year == agora.year
                        and data.month == agora.month
                    )

                    titulo = "📅 *Compras deste mês*"

                elif acao == "mes_passado":
                    if agora.month == 1:

                        mes = 12
                        ano = agora.year - 1

                    else:

                        mes = agora.month - 1
                        ano = agora.year

                    incluir = (
                        data.year == ano
                        and data.month == mes
                    )

                    titulo = "◀️ *Compras do mês passado*"

                elif acao == "ultimos_3_meses":
                    limite = agora - timedelta(
                        days=90
                    )

                    incluir = data >= limite

                    titulo = "📊 *Compras dos últimos 3 meses*"

                elif acao == "todas":
                    incluir = True

                    titulo = "🗂️ *Todas as compras*"

                if incluir:
                    compras_filtradas.append(
                        compra
                    )

            if not compras_filtradas:
                mensagem = (
                    f"{titulo}\n\n"
                    "📭 Nenhuma compra encontrada "
                    "neste período."
                )

            else:
                mensagem = (
                    f"{titulo}\n\n"
                    + self._formatar_compras(
                        compras_filtradas
                    )
                )

            botoes = [
                [
                    InlineKeyboardButton(
                        "📅 Escolher período",
                        callback_data="compras:periodo"
                    )
                ]
            ]

            teclado = InlineKeyboardMarkup(
                botoes
            )

            await query.edit_message_text(
                mensagem,
                parse_mode="Markdown",
                reply_markup=teclado
            )

        elif acao == "voltar":
            compras_recentes = compras[:3]

            mensagem = (
                "🛍️ *Últimas compras*\n\n"
                + self._formatar_compras(
                    compras_recentes
                )
            )

            botoes = []

            if len(compras) > 3:
                botoes.append([
                    InlineKeyboardButton(
                        "📋 Ver mais deste mês",
                        callback_data="compras:mais"
                    )
                ])

            botoes.append([
                InlineKeyboardButton(
                    "📅 Escolher período",
                    callback_data="compras:periodo"
                )
            ])

            teclado = InlineKeyboardMarkup(
                botoes
            )

            await query.edit_message_text(
                mensagem,
                parse_mode="Markdown",
                reply_markup=teclado
            )

    async def cancelar_compra(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        await query.answer()

        # Remove a compra
        context.user_data.pop(
            "compra_pendente",
            None
        )

        await query.edit_message_text(
            "Compra não registrada."
        )

    async def criar_categoria(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        await query.answer()

        # Ativa a criação de categoria
        # A próxima mensagem vai ser interpretada como o nome de uma nova categoria
        context.user_data["criando_categoria"] = True

        await query.edit_message_text(
            "Digite o nome da nova categoria:"
        )

    async def selecionar_categoria(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        await query.answer()

        # Pega o nome da categoria escolhida
        categoria = query.data.split(
            ":",
            1
        )[1]

        compra = context.user_data.get(
            "compra_pendente"
        )

        if compra is None:

            await query.edit_message_text(
                "❌ Não encontrei a compra pendente."
            )

            return

        usuario_id = update.effective_user.id

        service = CompraService(
            usuario_id,
            self.gemini_service
        )

        try:

            # Salva a compra
            service.confirmar_compra_com_categoria(
                compra,
                categoria
            )

            context.user_data.pop(
                "compra_pendente",
                None
            )

            await query.edit_message_text(
                f"✅ Compra registrada!\n"
                f"Categoria: {categoria}"
            )

        except Exception as e:

            print(
                f"Erro ao salvar compra: {e}"
            )

            await query.edit_message_text(
                "❌ Erro ao salvar a compra."
            )

    async def escolher_categoria(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        await query.answer()

        usuario_id = update.effective_user.id

        # Busca as categorias do banco do usuário
        service = CompraService(
            usuario_id,
            self.gemini_service
        )

        categorias = service.listar_categorias()

        botoes = []

        for categoria in categorias:

            botoes.append([
                InlineKeyboardButton(
                    categoria[1],
                    callback_data=f"categoria:{categoria[1]}"
                )
            ])

        # Cadastro de nova categoria
        botoes.append([
            InlineKeyboardButton(
                "➕ Criar categoria",
                callback_data="criar_categoria"
            )
        ])

        teclado = InlineKeyboardMarkup(botoes)

        await query.edit_message_text(
            "Escolha a categoria da compra:",
            reply_markup=teclado
        )