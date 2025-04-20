import asyncio
from aiogram import Bot, Dispatcher


from config import BOT_TOKEN
from handlers import rt

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

# TODO - СДЕЛАТЬ КНОПКИ "Я НАШЕЛ ПИТОМЦА"/"Я ИЩУ ПИТОМЦА" - !СРОЧНО
#      - ЗУЧИТЬ API
#      - НАЧАТЬ РАБОТУ С ОСНОВНОЙ ЧАСТЬЮ СРАВНИВАНИЯ
#      =========================
#      добавь мне при надобности:
#      -
#      -
#      -



async def main():
    dp.include_router(rt)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("бот остановлен")
