import numpy as np
from PIL import Image
from io import BytesIO
from sentence_transformers import SentenceTransformer
from pathlib import Path
from typing import List, Tuple


# Загружаем нейросетевую модель CLIP при старте
# Эта модель будет преобразовывать изображения в числовые векторы
try:
    model = SentenceTransformer('clip-ViT-B-32')
except Exception as e:
    logger.error(f"❌ Ошибка при загрузке CLIP: {str(e)}")
    raise


# =============================================
# ФУНКЦИЯ ДЛЯ ЗАГРУЗКИ И ОБРАБОТКИ ИЗОБРАЖЕНИЙ
# =============================================
def get_image_embedding(image_input) -> np.ndarray:
    try:
        # Если входные данные - bytes (BLOB из БД)
        if isinstance(image_input, bytes):
            logger.info("🔍 Loading image from BLOB data")
            image = Image.open(BytesIO(image_input))

        # Если путь к файлу или URL
        elif isinstance(image_input, (str, Path)):
            image_path = Path(image_input)
            logger.info(f"📂 Loading image: {image_path}")
            if not image_path.exists():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            image = Image.open(image_path)

        # Если уже объект Image
        elif isinstance(image_input, Image.Image):
            image = image_input

        else:
            raise ValueError("❌ Unsupported image input type")

        # Конвертация в RGB
        if image.mode != 'RGB':
            logger.debug("Converting image to RGB format")
            image = image.convert('RGB')

        # Преобразование в вектор
        logger.info("🖼️ Processing image with CLIP model...")
        return model.encode(image)

    except Exception as e:
        logger.error(f"🔥 Error processing image: {str(e)}")
        raise



# =============================================
# ФУНКЦИЯ СРАВНЕНИЯ ИЗОБРАЖЕНИЙ
# =============================================
def batch_compare(
        source_image: Image.Image,
        image_pairs: List[Tuple[int, Image.Image]]) -> List[Tuple[int, float]]:
    """
    Сравнивает исходное изображение со списком (request_id, image)
    Возвращает список кортежей (request_id, similarity_score)
    """
    results = []

    try:
        # Эмбеддинг исходного изображения
        source_embedding = get_image_embedding(source_image)
        source_embedding = source_embedding / np.linalg.norm(source_embedding)

        # Пакетная обработка
        for req_id, image in image_pairs:
            try:
                current_embedding = get_image_embedding(image)
                current_embedding = current_embedding / np.linalg.norm(current_embedding)

                similarity = float(np.dot(source_embedding, current_embedding))
                similarity = max(0.0, min(similarity, 1.0))

                results.append((req_id, similarity))

            except Exception as e:
                logger.warning(f"⏩ Skipping request {req_id}: {str(e)}")
                continue

        return sorted(results, key=lambda x: x[1], reverse=True)

    except Exception as e:
        logger.error(f"🔥 Batch comparison failed: {str(e)}")
        return []