# main/image_processor.py
import logging
from io import BytesIO
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from pillow_heif import register_heif_opener

from django.core.files.uploadedfile import UploadedFile, InMemoryUploadedFile
from django.core.exceptions import ValidationError
from django.conf import settings

register_heif_opener()

logger = logging.getLogger(__name__)

ALLOWED_IMAGE_FORMATS = {'JPEG', 'PNG', 'WEBP', 'GIF', 'BMP', 'HEIC', 'HEIF', 'MPO'}
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.heic', '.heif', '.mpo'}
MAX_IMAGE_SIZE = settings.IMAGE_MAX_SIZE_MB * 1024 * 1024 
IMAGE_QUALITY = settings.IMAGE_QUALITY
TARGET_MAX_DIMENSION = 2048

class ImageProcessingError(Exception):
    """Ошибка при обработке изображения"""
    pass

def validate_image_format(file: UploadedFile) -> None:
    """
    Проверяет, что загруженный файл - это изображение допустимого формата
    
    Args:
        file: Загруженный файл
        
    Raises:
        ValidationError: Если файл не является изображением или формат недопустим
    """
    file_ext = Path(file.name).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f'Неподдерживаемый формат файла. '
            f'Допустимые: {", ".join(ALLOWED_EXTENSIONS)}'
        )
    
    if file.size > MAX_IMAGE_SIZE:
        max_size_mb = MAX_IMAGE_SIZE / (1024 * 1024)
        raise ValidationError(
            f'Файл слишком большой. Максимум {max_size_mb:.1f}MB'
        )
    
    try:
        file.seek(0)
        img = Image.open(file)
        if getattr(img, "format", None) == "MPO":
            img.seek(0)
        img.verify()
        
        if img.format not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError(
                f'Неподдерживаемый формат изображения: {img.format}'
            )
    except (IOError, OSError) as e:
        raise ValidationError(f'Некорректный файл изображения: {str(e)}')
    except Exception as e:
        raise ValidationError(f'Ошибка при проверке изображения: {str(e)}')
    finally:
        file.seek(0)


def process_image(file: UploadedFile) -> InMemoryUploadedFile:
    """
    Обрабатывает изображение: конвертирует в JPG, сжимает, оптимизирует размер
    
    Args:
        file: Загруженное изображение
        
    Returns:
        InMemoryUploadedFile: Обработанное изображение в формате JPEG
        
    Raises:
        ImageProcessingError: Если произошла ошибка при обработке
    """
    try:
        validate_image_format(file)
        
        file.seek(0)
        img = Image.open(file)
        if getattr(img, "format", None) == "MPO":
            img.seek(0)
        
        if img.format in ('HEIC', 'HEIF') or img.mode in ('RGBA', 'LA', 'P'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = rgb_img
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        img = resize_image_if_needed(img)
        
        output = BytesIO()
        img.save(
            output,
            format='JPEG',
            quality=IMAGE_QUALITY,
            optimize=True,
            progressive=True
        )
        
        output.seek(0)
        
        original_name = Path(file.name).stem
        new_filename = f'{original_name}.jpg'
        
        processed_file = InMemoryUploadedFile(
            file=output,
            field_name=file.field_name,
            name=new_filename,
            content_type='image/jpeg',
            size=output.getbuffer().nbytes,
            charset=None
        )
        
        logger.info(f'Успешно обработано изображение: {new_filename} '
                   f'(размер: {processed_file.size / 1024:.1f}KB)')
        
        return processed_file
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f'Ошибка при обработке изображения: {str(e)}')
        raise ImageProcessingError(f'Не удалось обработать изображение: {str(e)}')


def resize_image_if_needed(img: Image.Image) -> Image.Image:
    """
    Уменьшает изображение если одна из сторон больше TARGET_MAX_DIMENSION
    
    Args:
        img: PIL Image объект
        
    Returns:
        PIL Image объект (возможно уменьшенное)
    """
    max_dim = max(img.size)
    
    if max_dim > TARGET_MAX_DIMENSION:
        ratio = TARGET_MAX_DIMENSION / max_dim
        new_size = (
            int(img.size[0] * ratio),
            int(img.size[1] * ratio)
        )
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        logger.info(f'Изображение уменьшено до {new_size}')
    
    return img


def get_image_dimensions(file: UploadedFile) -> Tuple[int, int]:
    """Получает размеры изображения без обработки"""
    try:
        file.seek(0)
        img = Image.open(file)
        if getattr(img, "format", None) == "MPO":
            img.seek(0)
        return img.size
    finally:
        file.seek(0)
