from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import sqlite3
from typing import List, Tuple
from aiogram import Bot
from aiogram.types import InlineKeyboardButton

from image_comparison import ImageComparator



class BackgroundProcessor:
    def __init__(self, bot: Bot, db_path: str = "database.db"):
        self.bot = bot
        self.db_path = db_path
        self.scheduler = AsyncIOScheduler()
        self.comparator = ImageComparator(db_path)
        self.NOTIFICATION_THRESHOLD = 0.85  # Порог для уведомлений

    async def start(self):
        """Запускает периодические задачи"""
        self.scheduler.add_job(
            self.process_all_requests,
            trigger=IntervalTrigger(minutes=1),
            next_run_time=datetime.now() + timedelta(seconds=1)
        )
        self.scheduler.start()


    async def stop(self):
        """Останавливает задачи"""
        self.scheduler.shutdown()

    async def process_all_requests(self):
        """Основная задача обработки"""


        try:
            # Получаем активные запросы за последние 30 дней
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id FROM requests 
                WHERE is_active = 1 
                AND created_at > datetime('now', '-30 days')
            """)
            request_ids = [row[0] for row in cursor.fetchall()]
            conn.close()

            # Обрабатываем каждый запрос
            for request_id in request_ids:
                await self.process_single_request(request_id)


        except Exception as e:
            print(f"Ошибка обработки: {str(e)}")

    async def process_single_request(self, request_id: int):
        """Обработка одного запроса"""
        try:
            # Сравниваем с противоположными запросами
            results = self.comparator.compare_with_database(request_id)

            # Фильтруем результаты по порогу
            filtered = [(rid, score) for rid, score in results if score >= self.NOTIFICATION_THRESHOLD]

            if filtered:
                await self.notify_users(request_id, filtered)

        except Exception as e:
            print(f"Ошибка обработки запроса {request_id}: {str(e)}")

    async def notify_users(self, source_id: int, matches: List[Tuple[int, float]]):
        """Отправка уведомлений пользователям"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Получаем информацию об исходном запросе
            cursor.execute("""
                SELECT user_id, request_type FROM requests 
                WHERE id = ?
            """, (source_id,))
            source_user_id, source_type = cursor.fetchone()

            # Для каждого совпадения
            for match_id, similarity in matches:
                # Проверяем, не отправлялось ли уже уведомление
                cursor.execute("""
                    SELECT 1 FROM notifications 
                    WHERE source_request = ? AND matched_request = ?
                """, (source_id, match_id))
                if cursor.fetchone():
                    continue  # Пропускаем уже отправленные уведомления

                # Получаем информацию о совпадении
                cursor.execute("""
                    SELECT user_id FROM requests 
                    WHERE id = ?
                """, (match_id,))
                match_user_id = cursor.fetchone()[0]

                # Получаем chat_id обоих пользователей
                cursor.execute("SELECT chat_id FROM users WHERE id = ?", (source_user_id,))
                source_chat_id = cursor.fetchone()[0]

                cursor.execute("SELECT chat_id FROM users WHERE id = ?", (match_user_id,))
                match_chat_id = cursor.fetchone()[0]

                # Формируем сообщения
                message_text = (
                    "🔔 Найдено совпадение!\n\n"
                    f"• Уровень совпадения: {similarity:.2%}\n"
                    "Хотите связаться с пользователем?"
                )

                # Создаем клавиатуры с кнопками
                source_kb = self._create_notification_kb(match_user_id)
                match_kb = self._create_notification_kb(source_user_id)

                # Отправляем уведомления только если они еще не были отправлены
                if not self.has_sent_notification(source_user_id, match_user_id):
                    await self.bot.send_message(
                        chat_id=source_chat_id,
                        text=message_text,
                        reply_markup=source_kb
                    )

                    await self.bot.send_message(
                        chat_id=match_chat_id,
                        text=message_text,
                        reply_markup=match_kb
                    )

                    # Записываем в историю уведомлений
                    cursor.execute("""
                        INSERT INTO notifications 
                        (source_request, matched_request, similarity)
                        VALUES (?, ?, ?)
                    """, (source_id, match_id, similarity))

            conn.commit()

        finally:
            conn.close()

    def has_sent_notification(self, user_a: int, user_b: int) -> bool:
        """Проверяет было ли уже отправлено уведомление между двумя пользователями"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 1 FROM notifications 
                WHERE (source_request IN (?, ?) AND matched_request IN (?, ?))
            """, (user_a, user_b, user_a, user_b))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    @staticmethod
    def _create_notification_kb(user_id: int):
        """Создает inline-клавиатуру для уведомления"""
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(  # Теперь класс распознается
                text="✅ Да, показать контакты",
                callback_data=f"show_contacts_{user_id}"
            ),
            InlineKeyboardButton(  # И здесь тоже
                text="❌ Нет, спасибо",
                callback_data="dismiss_notification"
            )
        )
        return builder.as_markup()


# Инициализация в основном файле бота
async def setup_background_tasks(bot: Bot):
    processor = BackgroundProcessor(bot)
    await processor.start()
    return processor
