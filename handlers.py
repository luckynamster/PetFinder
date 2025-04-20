from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
import texts

rt = Router()


@rt.message(CommandStart()) 
async def cmd_start(message: Message):
    await message.answer(texts.Start)
