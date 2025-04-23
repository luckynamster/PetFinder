import asyncio
from aiogram import Bot, Dispatcher

from config import BOT_TOKEN
from handlers import rt
from background_tasks import setup_background_tasks
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)


async def main():
    dp.include_router(rt)
    # Инициализация фоновых задач
    bg_processor = await setup_background_tasks(bot)

    try:
        await dp.start_polling(bot)
    finally:
        await bg_processor.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("бот остановлен")

