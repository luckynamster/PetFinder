import logging
import sqlite3
from io import BytesIO
from typing import List, Tuple
from PIL import Image

from image_processing import get_image_embedding, batch_compare

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ImageComparator:
    def __init__(self, db_path: str = "database.db"):
        self.db_path = db_path
        self.similarity_threshold = 0.75  # Порог схожести изображений

    def _get_opposite_request_type(self, request_type: str) -> str:
        """Возвращает противоположный тип запроса"""
        return "found" if request_type == "lost" else "lost"

    def _blob_to_image(self, blob_data: bytes) -> Image.Image:
        try:
            return Image.open(BytesIO(blob_data)).convert('RGB')  # Принудительная конвертация в RGB
        except Exception as e:
            logger.error(f"Ошибка конвертации BLOB: {str(e)}")
            raise ValueError("Invalid image data") from e

    def _get_comparable_requests(self, request_id: int, city: str, category: str) -> List[Tuple[int, bytes]]:
        """Получает список сравнимых запросов из БД с учетом города и категории"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Получаем тип исходного запроса
            cursor.execute("SELECT request_type FROM requests WHERE id = ?", (request_id,))
            request_type = cursor.fetchone()[0]
            opposite_type = "found" if request_type == "lost" else "lost"

            # Получаем противоположные запросы с учетом фильтров
            cursor.execute("""
                SELECT id, photo_data FROM requests 
                WHERE request_type = ?
                AND city = ?
                AND category = ?
                AND id != ?
                AND is_active = 1
            """, (opposite_type, city, category, request_id))

            return cursor.fetchall()
        finally:
            conn.close()

    def compare_with_database(self, request_id: int) -> List[Tuple[int, float]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Получаем данные исходного запроса
            cursor.execute("""
                SELECT photo_data, city, category 
                FROM requests 
                WHERE id = ?
            """, (request_id,))
            result = cursor.fetchone()

            if not result:
                logger.error(f"Request {request_id} not found")
                return []

            source_blob, city, category = result

            # Конвертируем исходное изображение
            try:
                source_image = self._blob_to_image(source_blob)  # <-- Исправлено здесь
            except ValueError as e:
                logger.error(f"Invalid source image: {str(e)}")
                return []

            # Получаем сравнимые запросы с фильтрами
            comparable = self._get_comparable_requests(request_id, city, category)
            if not comparable:
                return []

            # Подготавливаем данные в формате (request_id, Image)
            image_pairs = []
            for req_id, blob in comparable:
                try:
                    image = self._blob_to_image(blob)
                    image_pairs.append((req_id, image))
                except Exception as e:
                    logger.warning(f"Пропущен запрос {req_id}: {str(e)}")
                    continue

            # Выполняем сравнение
            results = batch_compare(source_image, image_pairs)  # <-- Теперь source_image определен

            # Фильтрация по порогу
            filtered = [
                (req_id, score)
                for req_id, score in results
                if score >= self.similarity_threshold
            ]

            return filtered

        except Exception as e:
            logger.error(f"Ошибка сравнения: {str(e)}")
            return []
        finally:
            conn.close()

    def save_comparison_results(self, request_id: int, results: List[Tuple[int, float]]):
        """Сохраняет результаты сравнения в БД"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Создаем таблицу для результатов если не существует
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_request INTEGER,
                    matched_request INTEGER,
                    similarity REAL,
                    compared_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(source_request) REFERENCES requests(id),
                    FOREIGN KEY(matched_request) REFERENCES requests(id)
                )
            """)

            # Вставляем новые записи
            for matched_id, similarity in results:
                cursor.execute("""
                    INSERT INTO matches (source_request, matched_request, similarity)
                    VALUES (?, ?, ?)
                """, (request_id, matched_id, similarity))

            conn.commit()
        finally:
            conn.close()
