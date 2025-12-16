"""
Management команда для прогрева кеша (cache warming)
"""
from django.core.management.base import BaseCommand
from main.models import SubRubric, Bb
from main.cache_utils import generate_cache_key, get_cached_or_set


class Command(BaseCommand):
    help = 'Прогрев кеша: предварительное заполнение часто используемых данных'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔥 Запуск прогрева кеша...'))
        
        self.stdout.write('📂 Кеширование рубрик...')
        cache_key = generate_cache_key('sidebar_rubrics')
        
        def fetch_rubrics():
            return list(SubRubric.objects.select_related('super_rubric').all())
        
        rubrics = get_cached_or_set(cache_key, fetch_rubrics, timeout=3600)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Закешировано рубрик: {len(rubrics)}'))
        
        self.stdout.write('🏠 Кеширование главной страницы...')
        cache_key = generate_cache_key('index_page', '', 1)
        
        def fetch_index_bbs():
            return list(Bb.objects.filter(is_active=True).select_related('rubric')[:5])
        
        bbs = get_cached_or_set(cache_key, fetch_index_bbs, timeout=300)
        self.stdout.write(self.style.SUCCESS(f'  ✓ Закешировано объявлений на главной: {len(bbs)}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Прогрев кеша завершён!'))
