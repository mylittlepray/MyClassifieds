"""
Management команда для тестирования кеша
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings


class Command(BaseCommand):
    help = 'Проверка работы кеширования'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Тестирование кеша...\n')
        
        # Информация о backend
        backend = settings.CACHES['default']['BACKEND']
        location = settings.CACHES['default']['LOCATION']
        self.stdout.write(f"Backend: {backend}")
        self.stdout.write(f"Location: {location}\n")
        
        # Тест 1: Простая запись/чтение
        self.stdout.write('Тест 1: Запись и чтение...')
        cache.set('test_key', 'test_value', timeout=60)
        value = cache.get('test_key')
        
        if value == 'test_value':
            self.stdout.write(self.style.SUCCESS('✅ Тест 1 пройден'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Тест 1 провален: получено {value}'))
        
        # Тест 2: Сложный объект
        self.stdout.write('\nТест 2: Кеширование списка...')
        test_data = [1, 2, 3, 4, 5]
        cache.set('test_list', test_data, timeout=60)
        cached_list = cache.get('test_list')
        
        if cached_list == test_data:
            self.stdout.write(self.style.SUCCESS('✅ Тест 2 пройден'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Тест 2 провален: получено {cached_list}'))
        
        # Тест 3: Удаление
        self.stdout.write('\nТест 3: Удаление ключа...')
        cache.set('test_delete', 'value')
        cache.delete('test_delete')
        deleted_value = cache.get('test_delete')
        
        if deleted_value is None:
            self.stdout.write(self.style.SUCCESS('✅ Тест 3 пройден'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Тест 3 провален: ключ не удален'))
        
        # Тест 4: TTL (Time To Live)
        self.stdout.write('\nТест 4: Проверка TTL...')
        import time
        cache.set('test_ttl', 'expires', timeout=2)
        
        value_before = cache.get('test_ttl')
        time.sleep(3)
        value_after = cache.get('test_ttl')
        
        if value_before == 'expires' and value_after is None:
            self.stdout.write(self.style.SUCCESS('✅ Тест 4 пройден'))
        else:
            self.stdout.write(self.style.ERROR(f'❌ Тест 4 провален: до={value_before}, после={value_after}'))
        
        self.stdout.write(self.style.SUCCESS('\n🎉 Тестирование завершено!'))
