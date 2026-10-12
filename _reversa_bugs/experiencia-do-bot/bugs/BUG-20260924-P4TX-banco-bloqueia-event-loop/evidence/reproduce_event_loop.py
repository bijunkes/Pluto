import asyncio
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[5]))

from src.telegram.telegram_bot import TelegramBot


async def main():
    bot = TelegramBot.__new__(TelegramBot)
    bot.ia_service = None
    update = SimpleNamespace(
        effective_user=SimpleNamespace(id=1),
        callback_query=None,
        message=SimpleNamespace(reply_text=AsyncMock()),
    )
    context = SimpleNamespace(user_data={})
    service = Mock()
    service.listar_compras.side_effect = lambda: (time.sleep(0.2) or [])
    marcacoes = []

    async def heartbeat():
        await asyncio.sleep(0.01)
        marcacoes.append(time.perf_counter())

    inicio = time.perf_counter()
    with patch("src.telegram.telegram_bot.CompraService", return_value=service):
        await asyncio.gather(bot.listar_compras(update, context), heartbeat())

    atraso = marcacoes[0] - inicio
    print(f"heartbeat_delay={atraso:.3f}")
    raise SystemExit(1 if atraso >= 0.1 else 0)


asyncio.run(main())
