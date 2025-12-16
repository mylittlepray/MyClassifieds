"""
Утилиты для работы с кешированием
"""
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Генерация уникального ключа кеша на основе префикса и параметров
    
    Args:
        prefix: Префикс ключа (например, 'rubrics', 'bb_detail')
        *args: Позиционные аргументы для формирования ключа
        **kwargs: Именованные аргументы для формирования ключа
    
    Returns:
        str: Хеш-ключ для кеша
    """
    key_data = {
        'prefix': prefix,
        'args': args,
        'kwargs': kwargs
    }
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_string.encode()).hexdigest()
    return f"{settings.CACHES['default']['KEY_PREFIX']}:{prefix}:{key_hash}"

def get_cached_or_set(
    cache_key: str,
    callback: Callable,
    timeout: Optional[int] = None,
    version: Optional[int] = None
) -> Any:
    """
    Получить данные из кеша или выполнить callback и закешировать результат
    
    Args:
        cache_key: Ключ кеша
        callback: Функция для получения данных, если их нет в кеше
        timeout: Время жизни кеша в секундах (None = default из settings)
        version: Версия ключа кеша (для инвалидации)
    
    Returns:
        Any: Закешированные или свежие данные
    """
    try:
        cached_data = cache.get(cache_key, version=version)
        if cached_data is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached_data
        
        logger.debug(f"Cache MISS: {cache_key}")
        fresh_data = callback()
        
        if timeout is None:
            timeout = settings.CACHES['default'].get('TIMEOUT', 300)
        
        cache.set(cache_key, fresh_data, timeout=timeout, version=version)
        return fresh_data
    
    except Exception as e:
        logger.error(f"Cache error for key {cache_key}: {e}")
        return callback()

def invalidate_cache(cache_key: str, version: Optional[int] = None):
    """
    Инвалидация (удаление) конкретного ключа кеша
    
    Args:
        cache_key: Ключ кеша для удаления
        version: Версия ключа
    """
    try:
        cache.delete(cache_key, version=version)
        logger.info(f"Cache invalidated: {cache_key}")
    except Exception as e:
        logger.error(f"Error invalidating cache key {cache_key}: {e}")

def invalidate_cache_pattern(pattern: str):
    """
    Инвалидация всех ключей, соответствующих паттерну (только для Redis)
    
    Args:
        pattern: Паттерн для поиска ключей (например, 'bboard:rubrics:*')
    """
    try:
        cache.delete_pattern(pattern)
        logger.info(f"Cache pattern invalidated: {pattern}")
    except AttributeError:
        logger.warning("delete_pattern not supported for current cache backend")
    except Exception as e:
        logger.error(f"Error invalidating cache pattern {pattern}: {e}")

def cache_view_result(timeout: int = 300, key_prefix: str = 'view'):
    """
    Декоратор для кеширования результата view-функции
    
    Args:
        timeout: Время жизни кеша в секундах
        key_prefix: Префикс для ключа кеша
    
    Usage:
        @cache_view_result(timeout=600, key_prefix='bb_list')
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Формируем ключ на основе URL и GET-параметров
            cache_key = generate_cache_key(
                key_prefix,
                request.path,
                request.GET.dict(),
                request.user.is_authenticated,
                request.user.pk if request.user.is_authenticated else None
            )
            
            def execute_view():
                return view_func(request, *args, **kwargs)
            
            return get_cached_or_set(cache_key, execute_view, timeout=timeout)
        
        return wrapper
    return decorator