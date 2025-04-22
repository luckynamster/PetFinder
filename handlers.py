from aiogram import Bot, Router, F, types
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile, ReplyKeyboardRemove, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
import sqlite3

import texts

rt = Router()


class Form(StatesGroup):
    request_type = State()
    photo = State()
    category = State()
    breed = State()
    gender = State()
    size = State()
    hair = State()
    city = State()
    chip_number = State()


def create_connection():
    return sqlite3.connect("database.db")


def cancel_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(
        text="❌ Отмена",
        callback_data="cancel"
    ))
    return builder.as_markup()


def main_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="Я ИЩУ ПИТОМЦА")],
            [types.KeyboardButton(text="Я НАШЕЛ ПИТОМЦА")]
        ],
        resize_keyboard=True,

    )


# Обработчик отмены
@rt.callback_query(F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.answer(texts.CANCEL, reply_markup=main_keyboard(),parse_mode="HTML")
    await callback.answer()


@rt.message(CommandStart())
async def cmd_start(message: Message):
    start_photo = FSInputFile("images/start_image.png")
    await message.answer_photo(
        start_photo,
        caption=texts.Start,
        reply_markup=main_keyboard(),
        parse_mode="HTML"
    )


@rt.message(F.text.in_(["Я ИЩУ ПИТОМЦА", "Я НАШЕЛ ПИТОМЦА"]))
async def handle_request_type(message: Message, state: FSMContext):
    request_type = "lost" if message.text == "Я ИЩУ ПИТОМЦА" else "found"
    await state.update_data(request_type=request_type)
    await state.set_state(Form.photo)
    await message.answer(
        "📸 Пожалуйста, отправьте фотографию животного",
        reply_markup=cancel_keyboard()
    )


@rt.message(Form.photo, F.photo)
async def handle_photo(message: Message, state: FSMContext, bot: Bot):
    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        photo_data = await bot.download_file(file.file_path)

        await state.update_data(photo_data=photo_data.read())
        await state.set_state(Form.category)

        await message.answer(
            "🐾 Введите вид животного (например: попугай, хомяк, кошка):",
            reply_markup=cancel_keyboard()
        )

    except Exception:
        await message.answer("❌ Ошибка обработки фото. Попробуйте еще раз.", reply_markup=cancel_keyboard())
        await state.clear()


@rt.message(Form.category)
async def handle_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await state.set_state(Form.breed)
    await message.answer(
        "🏷️ Введите породу животного (или 'дворняга' если неизвестно):",
        reply_markup=cancel_keyboard()
    )


@rt.message(Form.breed)
async def handle_breed(message: Message, state: FSMContext):
    await state.update_data(breed=message.text)
    await state.set_state(Form.gender)

    # Inline клавиатура для выбора пола
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(text="Самец", callback_data="male"),
        types.InlineKeyboardButton(text="Самка", callback_data="female"),
        types.InlineKeyboardButton(text="Неизвестно", callback_data="unknown")
    )
    builder.adjust(2)
    await message.answer(
        "🚻 Выберите пол животного:",
        reply_markup=builder.as_markup()
    )


# Обработчик выбора пола
@rt.callback_query(Form.gender, F.data.in_(["male", "female", "unknown"]))
async def handle_gender(callback: CallbackQuery, state: FSMContext):
    gender_map = {
        "male": "самец",
        "female": "самка",
        "unknown": "неизвестно"
    }
    await state.update_data(gender=gender_map[callback.data])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.delete()
    await state.set_state(Form.size)

    # Inline клавиатура для размера
    size_builder = InlineKeyboardBuilder()
    size_builder.add(
        types.InlineKeyboardButton(text="Маленький", callback_data="small"),
        types.InlineKeyboardButton(text="Средний", callback_data="medium"),
        types.InlineKeyboardButton(text="Большой", callback_data="large")
    )
    size_builder.adjust(2)

    await callback.message.answer(
        "📏 Выберите размер животного:",
        reply_markup=size_builder.as_markup()
    )
    await callback.answer()


# Обработчик выбора размера
@rt.callback_query(Form.size, F.data.in_(["small", "medium", "large"]))
async def handle_size(callback: CallbackQuery, state: FSMContext):
    size_map = {
        "small": "маленький",
        "medium": "средний",
        "large": "большой"
    }
    await state.update_data(size=size_map[callback.data])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.delete()
    await state.set_state(Form.hair)

    # Inline клавиатура для шерсти
    hair_builder = InlineKeyboardBuilder()
    hair_builder.add(
        types.InlineKeyboardButton(text="Короткая", callback_data="short"),
        types.InlineKeyboardButton(text="Длинная", callback_data="long"),
        types.InlineKeyboardButton(text="Нет", callback_data="none")
    )
    hair_builder.adjust(2)

    await callback.message.answer(
        "🧶 Выберите тип шерсти:",
        reply_markup=hair_builder.as_markup()
    )
    await callback.answer()


# Обработчик выбора шерсти
@rt.callback_query(Form.hair, F.data.in_(["short", "long", "none"]))
async def handle_hair(callback: CallbackQuery, state: FSMContext):
    hair_map = {
        "short": "короткая",
        "long": "длинная",
        "none": "нет"
    }
    await state.update_data(hair=hair_map[callback.data])
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.delete()
    await state.set_state(Form.city)
    await callback.message.answer(
        "🌆 Введите город, где животное было потеряно/найдено:",
        reply_markup=cancel_keyboard()
    )
    await callback.answer()


@rt.message(Form.city)
async def handle_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await state.set_state(Form.chip_number)
    await message.answer(
        "🔢 Если известно, введите номер чипа (или отправьте /skip):",
        reply_markup=cancel_keyboard()
    )


@rt.message(Form.chip_number, Command("skip"))
@rt.message(Form.chip_number)
async def handle_chip_number(message: Message, state: FSMContext):
    chip_number = message.text if message.text != "/skip" else None
    await state.update_data(chip_number=chip_number)

    data = await state.get_data()
    conn = create_connection()

    try:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (chat_id) VALUES (?)", (message.from_user.id,))
        cursor.execute("SELECT id FROM users WHERE chat_id = ?", (message.from_user.id,))
        user_id = cursor.fetchone()[0]

        cursor.execute('''
            INSERT INTO requests (
                user_id, request_type, photo_data, category, breed,
                gender, size, hair, city, chip_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            data['request_type'],
            data['photo_data'],
            data.get('category'),
            data.get('breed'),
            data.get('gender'),
            data.get('size'),
            data.get('hair'),
            data.get('city'),
            chip_number
        ))

        conn.commit()
        await message.answer("✅ Данные сохранены! Начинаем поиск...", reply_markup=main_keyboard())

    except sqlite3.Error as e:
        await message.answer(f"❌ Ошибка сохранения данных: {str(e)}", reply_markup=cancel_keyboard())

    finally:
        conn.close()
        await state.clear()
