from django.urls import path
from .views import (
    AllApprovedArticlesListAPIView, RecommendedArticlesAPIView,
    ArticlesMostReactionScoreListAPIView, ReactionGenericAPIView, ArticleRetrieveAPIView
)

urlpatterns = [
    path('feed/', AllApprovedArticlesListAPIView.as_view(), name='all-articles'),    
    path('recommended/', RecommendedArticlesAPIView.as_view(), name="articles-recommended"),
    path('trending/', ArticlesMostReactionScoreListAPIView.as_view(), name='articles-trending'),
    path('<int:article_id>/react/', ReactionGenericAPIView.as_view(), name="article-reaction"),
    path('<int:pk>/', ArticleRetrieveAPIView.as_view(), name='patient-article-detail'), # مشترك للقراءة
]