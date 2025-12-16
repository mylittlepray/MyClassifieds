"""
API view-функции с кешированием (синхронные, совместимы с ATOMIC_REQUESTS)
"""
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from .models import SubRubric, Bb
from .cache_utils import generate_cache_key, get_cached_or_set
import logging

logger = logging.getLogger(__name__)

CACHE_TIMEOUT_RUBRICS = 3600
CACHE_TIMEOUT_POPULAR_BBS = 600

@require_http_methods(["GET"])
def api_rubrics(request):
    """
    API для получения списка рубрик с кешированием
    GET /api/async/rubrics/
    """
    cache_key = generate_cache_key('api_rubrics', 'all')
    
    def fetch_rubrics():
        rubrics = list(
            SubRubric.objects.select_related('super_rubric')
            .values('id', 'name', 'super_rubric__name')
            .order_by('super_rubric__order', 'super_rubric__name', 'order', 'name')
        )
        logger.info(f"Fetched {len(rubrics)} rubrics from DB")
        return rubrics
    
    rubrics = get_cached_or_set(cache_key, fetch_rubrics, timeout=CACHE_TIMEOUT_RUBRICS)
    
    return JsonResponse({'rubrics': rubrics}, safe=False)

@require_http_methods(["GET"])
def api_popular_bbs(request):
    """
    API для получения популярных объявлений с кешированием
    GET /api/async/popular/?limit=10
    """
    limit = int(request.GET.get('limit', 10))
    cache_key = generate_cache_key('api_popular_bbs', limit)
    
    def fetch_popular_bbs():
        bbs = list(
            Bb.objects.filter(is_active=True)
            .select_related('rubric', 'author')
            .order_by('-created_at')[:limit]
            .values(
                'id', 'title', 'content', 'price', 
                'created_at', 'rubric__name', 'author__username'
            )
        )
        logger.info(f"Fetched {len(bbs)} popular bbs from DB")
        return bbs
    
    bbs = get_cached_or_set(cache_key, fetch_popular_bbs, timeout=CACHE_TIMEOUT_POPULAR_BBS)
    
    return JsonResponse({'bbs': bbs}, safe=False)

@require_http_methods(["GET"])
def api_bb_detail(request, pk):
    """
    API для получения деталей объявления с кешированием
    GET /api/async/bb/<pk>/
    """
    cache_key = generate_cache_key('api_bb_detail', pk)
    
    def fetch_bb_detail():
        try:
            bb = Bb.objects.select_related('rubric', 'author').get(pk=pk, is_active=True)
            additional_images = list(bb.additionalimage_set.all().values('image'))
            
            data = {
                'id': bb.id,
                'title': bb.title,
                'content': bb.content,
                'price': float(bb.price),
                'contacts': bb.contacts,
                'created_at': bb.created_at.isoformat(),
                'rubric': bb.rubric.name,
                'author': bb.author.username,
                'image': bb.image.url if bb.image else None,
                'additional_images': [img['image'] for img in additional_images]
            }
            logger.info(f"Fetched bb #{pk} from DB")
            return data
        except Bb.DoesNotExist:
            return None
    
    bb_data = get_cached_or_set(cache_key, fetch_bb_detail, timeout=300)
    
    if bb_data is None:
        return JsonResponse({'error': 'Объявление не найдено'}, status=404)
    
    return JsonResponse(bb_data)