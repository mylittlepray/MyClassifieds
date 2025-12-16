"""
URL-маршруты для API endpoints с кешированием
"""
from django.urls import path
from . import api_views

app_name = 'async_api'

urlpatterns = [
    path('rubrics/', api_views.api_rubrics, name='rubrics'),
    path('popular/', api_views.api_popular_bbs, name='popular'),
    path('bb/<int:pk>/', api_views.api_bb_detail, name='bb_detail'),
]
