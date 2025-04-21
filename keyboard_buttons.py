from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

choose = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Я НАШЕЛ ПИТОМЦА"), KeyboardButton(text="Я ИЩУ ПИТОМЦА")]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите здесь:", # это меняет текст в поле ввода

)
