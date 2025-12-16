"""
Management команда для очистки кеша
"""
from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Полная очистка кеша приложения'

    def handle(self, *args, **options):
        self.stdout.write('Очистка кеша...')
        cache.clear()
        self.stdout.write(self.style.SUCCESS('✓ Кеш успешно очищен'))
