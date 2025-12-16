from django.dispatch import Signal, receiver
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache
from .models import Comment, Bb, SubRubric
from .cache_utils import generate_cache_key, invalidate_cache_pattern

from .utilities import send_new_comment_notification 
from .utilities import send_activation_notification

post_register = Signal()

@receiver(post_register)
def post_register_dispatcher(sender, **kwargs):
    send_activation_notification(kwargs['instance'])

@receiver(post_save, sender=Comment)
def post_save_dispatcher(sender, **kwargs):
    """Обработка сохранения комментария + инвалидация кеша"""
    instance = kwargs['instance']
    author = instance.bb.author
    
    if kwargs['created'] and author.send_messages:
        send_new_comment_notification(instance)
    
    cache_key_rating = generate_cache_key('bb_rating', instance.bb.pk)
    cache.delete(cache_key_rating)

@receiver([post_save, post_delete], sender=Bb)
def invalidate_bb_cache(sender, instance, **kwargs):
    """
    Инвалидация кеша при изменении/удалении объявления
    """
    cache_key_bb = generate_cache_key('bb_detail', instance.pk)
    cache.delete(cache_key_bb)
    
    cache_key_rating = generate_cache_key('bb_rating', instance.pk)
    cache.delete(cache_key_rating)
    
    invalidate_cache_pattern(f'bboard:rubric_bbs:{instance.rubric.pk}:*')
    
    invalidate_cache_pattern('bboard:index_page:*')

@receiver([post_save, post_delete], sender=SubRubric)
def invalidate_rubrics_cache(sender, instance, **kwargs):
    """
    Инвалидация кеша рубрик при их изменении
    """
    invalidate_cache_pattern('bboard:rubrics:*')
