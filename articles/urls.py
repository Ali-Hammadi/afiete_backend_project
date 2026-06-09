# Path: articles/urls.py

from django.urls import path
from .views import (
    ArticleListAPIView,
    ArticleCreateAPIView,
    ArticleRetrieveAPIView,
    DeleteArticleGenericAPIView,
    AllApprovedArticlesListAPIView,
    RecommendedArticlesAPIView,
    ArticlesMostReactionScoreListAPIView,
    ReactionGenericAPIView,
    ArticleUpdateAPIView
)

urlpatterns = [
    path('', ArticleListAPIView.as_view(), name="personal-articles"),
    path('create/', ArticleCreateAPIView.as_view(), name='add-article'),
    path('<int:pk>/', ArticleRetrieveAPIView.as_view(), name='article'),
    path('update/<int:pk>/', ArticleUpdateAPIView.as_view(), name='article-update'), # الرابط الجديد الخاص بالتعديل
    path('remove/<int:article_id>', DeleteArticleGenericAPIView.as_view(), name='article-delete'),
    path('all/', AllApprovedArticlesListAPIView.as_view(), name='all-articles'),    
    path('recommended/', RecommendedArticlesAPIView.as_view(), name="articles-recommended"),
    path('trending/', ArticlesMostReactionScoreListAPIView.as_view(), name='articles-trending'),
    path('<int:article_id>/react', ReactionGenericAPIView.as_view(), name="article-reaction"),
]