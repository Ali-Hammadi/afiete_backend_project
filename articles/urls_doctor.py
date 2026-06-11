from django.urls import path
from .views import ArticleListAPIView, ArticleCreateAPIView, ArticleUpdateAPIView, DeleteArticleGenericAPIView, ArticleRetrieveAPIView

urlpatterns = [
    path('my-articles/', ArticleListAPIView.as_view(), name="personal-articles"),
    path('create/', ArticleCreateAPIView.as_view(), name='add-article'),
    path('update/<int:pk>/', ArticleUpdateAPIView.as_view(), name='article-update'), 
    path('remove/<int:article_id>/', DeleteArticleGenericAPIView.as_view(), name='article-delete'),
    path('<int:pk>/', ArticleRetrieveAPIView.as_view(), name='doctor-article-detail'), # مشترك للقراءة
]