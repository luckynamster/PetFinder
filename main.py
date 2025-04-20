import asyncio
import texts

from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message

from config import BOT_TOKEN

dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(texts.Start)



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
