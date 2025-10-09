"""
URLs для приложения digest.
"""

from django.urls import path
from . import views

app_name = 'digest'

urlpatterns = [
    # Главная страница
    path('', views.dashboard, name='dashboard'),
    
    # Запуски дайджеста
    path('runs/', views.DigestRunListView.as_view(), name='digestrun_list'),
    path('runs/<int:pk>/', views.DigestRunDetailView.as_view(), name='digestrun_detail'),
    
    # Статьи
    path('articles/', views.ArticleListView.as_view(), name='article_list'),
    
    # Сгенерированные посты
    path('posts/', views.GeneratedPostListView.as_view(), name='generatedpost_list'),
]
