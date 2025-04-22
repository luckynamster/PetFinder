# image_processing.py
import numpy as np
from PIL import Image
import requests
from io import BytesIO
from sentence_transformers import SentenceTransformer
from pathlib import Path
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем нейросетевую модель CLIP при старте
# Эта модель будет преобразовывать изображения в числовые векторы
try:
    model = SentenceTransformer('clip-ViT-B-32')
    logger.info("✅ CLIP загружен успешно")
except Exception as e:
    logger.error(f"❌ Ошибка при загрузке CLIP: {str(e)}")
    raise


# =============================================
# ФУНКЦИЯ ДЛЯ ЗАГРУЗКИ И ОБРАБОТКИ ИЗОБРАЖЕНИЙ
# =============================================
def get_image_embedding(image_input) -> np.ndarray:

    try:
        # --------------------------------------------------
        # ЗАГРУЗКА ИЗОБРАЖЕНИЯ ИЗ РАЗНЫХ ИСТОЧНИКОВ
        # --------------------------------------------------
        if isinstance(image_input, (str, Path)):

                image_path = Path(image_input)
                logger.info(f"📂 Loading image: {image_path}")
                if not image_path.exists():
                    raise FileNotFoundError(f"Image file not found: {image_path}")
                image = Image.open(image_path)

        else:
            raise ValueError("❌ Unsupported image input type")

        # --------------------------------------------------
        # ПРЕДВАРИТЕЛЬНАЯ ОБРАБОТКА ИЗОБРАЖЕНИЯ
        # --------------------------------------------------
        # Конвертируем в RGB, если изображение в другом формате
        if image.mode != 'RGB':
            logger.debug("Converting image to RGB format")
            image = image.convert('RGB')

        # --------------------------------------------------
        # ПРЕОБРАЗОВАНИЕ В ВЕКТОР С ПОМОЩЬЮ CLIP
        # --------------------------------------------------
        logger.info("🖼️ Processing image with CLIP model...")
        return model.encode(image)

    except Exception as e:
        logger.error(f"🔥 Error processing image: {str(e)}")
        raise ValueError(f"Image processing failed: {str(e)}") from e


# =============================================
# ФУНКЦИЯ СРАВНЕНИЯ ИЗОБРАЖЕНИЙ
# =============================================
def batch_compare(source_image, image_list: list) -> list[tuple[str, float]]:
    """

        source_image: (загружаемая пользователем)
        image_list: (лист изображений для сравнивания)

    Возвращает:
        Список кортежей в формате [(путь_к_изображению, оценка_схожести), ...],
        отсортированный по убыванию схожести (от 1.0 до 0.0)
    """
    if not image_list:
        logger.warning("⚠️ Лист изображений пуст")
        return []

    results = []

    try:
        # =============================================
        # ПОДГОТОВКА ИСХОДНОГО ИЗОБРАЖЕНИЯ
        # =============================================
        logger.info(f"🔍 Подготовка для сравнивания...")
        source_embedding = get_image_embedding(source_image)
        source_embedding = source_embedding / np.linalg.norm(source_embedding)

        # =============================================
        # ПАКЕТНАЯ ОБРАБОТКА СПИСКА
        # =============================================
        logger.info(f"🔄 Обрабатывается {len(image_list)} изображений...")

        for img_path in image_list:
            try:
                # 2.1. Получаем вектор текущего изображения
                current_embedding = get_image_embedding(img_path)
                current_embedding = current_embedding / np.linalg.norm(current_embedding)

                # 2.2. Вычисляем косинусную схожесть
                similarity = float(np.dot(source_embedding, current_embedding))
                similarity = max(0.0, min(similarity, 1.0))  # Ограничиваем [0, 1]

                # 2.3. Сохраняем результат
                results.append((str(img_path), similarity))

                logger.debug(f"Обработано: {img_path} → {similarity:.2f}")

            except Exception as e:
                logger.warning(f"⏩ Пропущенно {img_path}: {str(e)}")
                continue

        # =============================================
        # СОРТИРОВКА И ВОЗВРАТ РЕЗУЛЬТАТОВ
        # =============================================
        logger.info("📊 Сортировка по степени схожести...")
        sorted_results = sorted(results, key=lambda x: x[1], reverse=True)

        return sorted_results

    except Exception as e:
        logger.error(f"🔥 Не удалось - ошибка: {str(e)}")
        return []