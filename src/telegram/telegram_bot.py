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

        # Envia o link mágico de acesso ao dashboard web
        self.app.add_handler(
            CommandHandler(
                "dashboard",
                self.abrir_dashboard
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
        
        # Não confirmar -> Escolher categoria
        self.app.add_handler(
            CallbackQueryHandler(
                self.escolher_categoria,
                pattern="^escolher_categoria$"
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
        
        # Cancela a compra
        self.app.add_handler(
            CallbackQueryHandler(
                self.cancelar_compra,
                pattern="^cancelar$"
            )
        )

    async def start(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        await update.message.reply_text(
            "Olá! Eu sou o Pluto\n"
            "Envie uma mensagem com uma compra para começar.\n\n"
            "Use /dashboard para abrir seu painel web."
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

    def iniciar(self):

        print(
            "Pluto Telegram iniciado!"
        )

        self.app.run_polling()
        
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

        categorias = service.database.listar_categorias()

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