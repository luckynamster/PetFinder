from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
import texts

rt = Router()


@rt.message(CommandStart()) 
async def cmd_start(message: Message):
    startPhoto = FSInputFile("images/start_image.png")
    await message.answer_photo(startPhoto,
                               caption=texts.Start,
                               parse_mode = "html"
    )
