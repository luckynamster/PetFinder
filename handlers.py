from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, InputFile
import texts

rt = Router()


@rt.message(CommandStart()) 
async def cmd_start(message: Message):
    photo = InputFile("images\start_image.png")
    await message.answer_photo(
        photo=photo,
        caption=texts.Start)
