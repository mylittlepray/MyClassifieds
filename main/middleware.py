import logging

from django.contrib.messages import constants as message_constants
from .models import SubRubric
from .cache_utils import generate_cache_key, get_cached_or_set

logger = logging.getLogger(__name__)

def bboard_context_processor(request):
    """Контекстный процессор для глобальных переменных с кешированием"""
    
    cache_key = generate_cache_key('sidebar_rubrics')
    
    def get_rubrics():
        return SubRubric.objects.select_related('super_rubric').all()
    
    rubrics = get_cached_or_set(cache_key, get_rubrics, timeout=3600)
    
    context = {
        'rubrics': rubrics,
        'keyword': '',
        'all': '',
        'MESSAGE_LEVELS': {
            'DEBUG': message_constants.DEBUG,
            'INFO': message_constants.INFO,
            'SUCCESS': message_constants.SUCCESS,
            'WARNING': message_constants.WARNING,
            'ERROR': message_constants.ERROR,
        }
    }
    
    if 'keyword' in request.GET:
        keyword = request.GET['keyword']
        if keyword:
            context['keyword'] = '?keyword=' + keyword
            context['all'] = context['keyword']
    
    if 'page' in request.GET:
        page = request.GET['page']
        if page != '1':
            if context['all']:
                context['all'] += '&page=' + page
            else:
                context['all'] = '?page=' + page
    
    return context

class ImageUploadErrorMiddleware:
    """Middleware для логирования ошибок при загрузке изображений"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Логируем ошибки 413 (Request Entity Too Large)
        if response.status_code == 413:
            logger.warning(
                f'Request too large from {request.META.get("REMOTE_ADDR")} '
                f'Content-Length: {request.META.get("CONTENT_LENGTH")}'
            )
        
        return response