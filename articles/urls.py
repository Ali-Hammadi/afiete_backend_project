from django.urls import path
from .views import *
urlpatterns = [
    path('', ArticleListAPIView.as_view(), name="personal-articles" ),
    path('create/', ArticleCreateAPIView.as_view(), name='add-article'),
    path('<int:pk>/', ArticleRetrieveAPIView.as_view(), name='article'),
    path('remove/<int:article_id>', DeleteArticleGenericAPIView.as_view(), name='article-delete'),
    path('recommended/', RecommendedArticlesAPIView.as_view(), name="articles-recommended"),
    path('trending/', ArticlesMostReactionScoreListAPIView.as_view(), name='articles-trending'),
    path('<int:article_id>/react', ReactionGenericAPIView.as_view(), name = "article-reaction"),
]