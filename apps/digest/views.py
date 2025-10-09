"""
Views для приложения digest.
"""

from django.shortcuts import render
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import DigestRun, Article, GeneratedPost


class DigestRunListView(LoginRequiredMixin, ListView):
    """Список запусков дайджеста."""
    model = DigestRun
    template_name = 'digest/digestrun_list.html'
    context_object_name = 'digest_runs'
    paginate_by = 20


class DigestRunDetailView(LoginRequiredMixin, DetailView):
    """Детальная информация о запуске дайджеста."""
    model = DigestRun
    template_name = 'digest/digestrun_detail.html'
    context_object_name = 'digest_run'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавляем статьи этого запуска
        context['articles'] = self.object.articles.select_related('source').all()
        return context


class ArticleListView(LoginRequiredMixin, ListView):
    """Список всех статей."""
    model = Article
    template_name = 'digest/article_list.html'
    context_object_name = 'articles'
    paginate_by = 50
    
    def get_queryset(self):
        return Article.objects.select_related('source', 'digest_run').all()


class GeneratedPostListView(LoginRequiredMixin, ListView):
    """Список сгенерированных постов."""
    model = GeneratedPost
    template_name = 'digest/generatedpost_list.html'
    context_object_name = 'posts'
    paginate_by = 50
    
    def get_queryset(self):
        return GeneratedPost.objects.select_related('article').all()


def dashboard(request):
    """Дашборд приложения."""
    if request.user.is_authenticated:
        # Статистика для дашборда
        total_runs = DigestRun.objects.count()
        total_articles = Article.objects.count()
        total_posts = GeneratedPost.objects.count()
        
        # Последние запуски
        recent_runs = DigestRun.objects.order_by('-started_at')[:5]
        
        # Самые интересные статьи
        top_articles = Article.objects.filter(
            is_relevant=True
        ).order_by('-interest_score')[:10]
        
        context = {
            'total_runs': total_runs,
            'total_articles': total_articles,
            'total_posts': total_posts,
            'recent_runs': recent_runs,
            'top_articles': top_articles,
        }
        return render(request, 'digest/dashboard.html', context)
    else:
        return render(request, 'digest/landing.html')
