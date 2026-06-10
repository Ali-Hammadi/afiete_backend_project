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
    # --- تصفح المريض (api/patient/articles/) ---
    path('feed/', AllApprovedArticlesListAPIView.as_view(), name='all-articles'),    
    path('recommended/', RecommendedArticlesAPIView.as_view(), name="articles-recommended"),
    path('trending/', ArticlesMostReactionScoreListAPIView.as_view(), name='articles-trending'),
    path('<int:article_id>/react/', ReactionGenericAPIView.as_view(), name="article-reaction"),

    # --- إدارة الطبيب لمقالاته (api/doctor/articles/) ---
    path('my-articles/', ArticleListAPIView.as_view(), name="personal-articles"),
    path('create/', ArticleCreateAPIView.as_view(), name='add-article'),
    path('update/<int:pk>/', ArticleUpdateAPIView.as_view(), name='article-update'), 
    path('remove/<int:article_id>/', DeleteArticleGenericAPIView.as_view(), name='article-delete'),
    
    # مشترك للقراءة
    path('<int:pk>/', ArticleRetrieveAPIView.as_view(), name='article-detail'),
]