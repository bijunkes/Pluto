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
from src.database.database import Database


class TelegramBot:

    def __init__(self):

        load_dotenv()

        self.token = os.environ["TELEGRAM_BOT_TOKEN"]

        # Serviços da aplicação
        self.gemini_service = GeminiService()
        self.database = Database()

        self.compra_service = CompraService(
            self.gemini_service,
            self.database
        )

        # Cria aplicação do Telegram
        self.app = (
            Application
            .builder()
            .token(self.token)
            .build()
        )

        self._configurar_handlers()

    def _configurar_handlers(self):

        self.app.add_handler(
            CommandHandler(
                "start",
                self.start
            )
        )

        # Fotos
        self.app.add_handler(
            MessageHandler(
                filters.PHOTO,
                self.receber_foto
            )
        )

        # Mensagens de texto
        self.app.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.receber_mensagem
            )
        )

        # Confirmar compra
        self.app.add_handler(
            CallbackQueryHandler(
                self.confirmar_compra,
                pattern="^confirmar$"
            )
        )

        # Cancelar compra
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
            "Olá! Eu sou o Pluto 💰\n"
            "Envie uma mensagem com uma compra para começar."
        )

    async def receber_mensagem(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        mensagem = update.message.text

        await update.message.reply_text(
            "🔎 Analisando sua compra..."
        )

        try:

            resultado = self.compra_service.processar_compra(
                mensagem=mensagem
            )

        except Exception as e:

            print(f"Erro ao analisar compra: {e}")

            await update.message.reply_text(
                "❌ Não consegui analisar a compra agora. "
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

        await update.message.reply_text(
            "🔎 Analisando sua compra..."
        )

        foto = update.message.photo[-1]

        arquivo = await foto.get_file()

        caminho = "produto.jpg"

        await arquivo.download_to_drive(caminho)

        try:

            resultado = self.compra_service.processar_compra(
                imagem_path=caminho,
                mensagem=mensagem
            )

        except Exception as e:

            print(f"Erro ao analisar imagem: {e}")

            await update.message.reply_text(
                "❌ Não consegui analisar a imagem agora. "
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

        # Guarda a compra até o usuário confirmar
        context.user_data["compra_pendente"] = resultado

        botoes = [
            [
                InlineKeyboardButton(
                    "✅ Confirmar",
                    callback_data="confirmar"
                ),
                InlineKeyboardButton(
                    "❌ Cancelar",
                    callback_data="cancelar"
                )
            ]
        ]

        teclado = InlineKeyboardMarkup(botoes)

        await update.message.reply_text(
            f"🛍️ Compra identificada:\n\n"
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
                "❌ Não encontrei uma compra pendente."
            )

            return

        try:

            self.compra_service.confirmar_compra(
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

            print(f"Erro ao salvar compra: {e}")

            await query.edit_message_text(
                "❌ Não foi possível registrar a compra."
            )

    async def cancelar_compra(
        self,
        update: Update,
        context: ContextTypes.DEFAULT_TYPE
    ):

        query = update.callback_query

        await query.answer()

        context.user_data.pop(
            "compra_pendente",
            None
        )

        await query.edit_message_text(
            "❌ Compra não registrada."
        )

    def iniciar(self):

        print("Pluto Telegram iniciado!")

        self.app.run_polling()