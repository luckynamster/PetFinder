import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("бот остановлен")
