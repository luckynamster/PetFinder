from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile

import keyboard_buttons
import texts
rt = Router()


@rt.message(CommandStart()) 
async def cmd_start(message: Message):
    startPhoto = FSInputFile("images/start_image.png")
    await message.answer_photo(startPhoto,
                               caption=texts.Start,
                               parse_mode = "HTML",
                               reply_markup=keyboard_buttons.choose #вызов кнопочек снизу
    )

