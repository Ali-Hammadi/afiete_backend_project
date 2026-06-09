# Path: articles/views.py

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Case, When, IntegerField
from users.models import User
from users.permissions import IsDoctor, IsPatient

from .serializers import (
    ArticaleCraeteSerializer,
    ArticleRetrieveSerializer,
    ArticleSerializer,
    ReactionSerializer,
    DeleteArticleSerializer,
    ArticleUpdateSerializer
)
from .models import Article, Reaction
from .recommender import recommend_articles
from .pagination import ArticlePagination

class ArticleCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = ArticaleCraeteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "message": "Article added, please wait until review it"
        }, status=status.HTTP_201_CREATED)

class ArticleRetrieveAPIView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ArticleRetrieveSerializer
    
    def get_queryset(self):
        return Article.objects.with_reactions(user=self.request.user).filter(status="Approved")

class ArticleListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = ArticleRetrieveSerializer
    pagination_class = ArticlePagination

    def get_queryset(self):
        username = self.request.query_params.get('author_username', None)
        objs = Article.objects.with_reactions(user=self.request.user)
        
        if username:
            user = get_object_or_404(User, username=username)
            return objs.filter(author=user.doctor, status="Approved").order_by('-score')
        
        return objs.filter(author=self.request.user.doctor).order_by('-created_at')

class RecommendedArticlesAPIView(generics.ListAPIView):
    pagination_class = ArticlePagination
    serializer_class = ArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsPatient]

    def get_queryset(self):
        recommended_ids = recommend_articles(patient=self.request.user.patient)
        
        order = Case(
            *[When(id=aid, then=pos) for pos, aid in enumerate(recommended_ids)],
            output_field=IntegerField()
        )
        
        return Article.objects.with_reactions(user=self.request.user)\
            .filter(id__in=recommended_ids, status='Approved')\
            .annotate(relevance_order=order)\
            .order_by('relevance_order', '-score')

class AllApprovedArticlesListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ArticleSerializer
    pagination_class = ArticlePagination

    def get_queryset(self):
        return Article.objects.with_reactions(user=self.request.user).filter(status="Approved").order_by('-created_at')

class ArticlesMostReactionScoreListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ArticleSerializer
    pagination_class = ArticlePagination

    def get_queryset(self):
        return Article.objects.with_reactions(user=self.request.user).filter(status="Approved").order_by('-score', '-likes')

# الـ View الجديد المخصص لتعديل المقالة وإعادتها لقسم المراجعة للأدمن
class ArticleUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = ArticleUpdateSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        # يضمن ألا يقوم الطبيب بتعديل أي مقال لا يخصه
        return Article.objects.filter(author=self.request.user.doctor)

class ReactionGenericAPIView(generics.GenericAPIView):
    serializer_class = ReactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, article_id):
        user = request.user
        reaction_type = request.data.get('reaction')
        article = get_object_or_404(Article, id=article_id)
        
        if article.status != "Approved":
            return Response({"error": "Article not approved"}, status=status.HTTP_400_BAD_REQUEST)
        
        exist = Reaction.objects.filter(user=user, article=article).first()
        if exist:
            if exist.reaction == reaction_type:
                exist.delete()
                return Response({"message": f"{reaction_type} removed"}, status=status.HTTP_200_OK)
            else:
                exist.reaction = reaction_type
                exist.save()
                return Response({"message": f"{reaction_type} updated"}, status=status.HTTP_200_OK)
        
        Reaction.objects.create(user=user, article=article, reaction=reaction_type)
        return Response({"message": f"{reaction_type} added"}, status=status.HTTP_210_CREATED if status.HTTP_201_CREATED else status.HTTP_200_OK)

class DeleteArticleGenericAPIView(generics.GenericAPIView):
    serializer_class = DeleteArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor]

    def delete(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        if article.author != request.user.doctor:
            return Response({"error": "Article not related to author"}, status=status.HTTP_400_BAD_REQUEST)
        
        article.delete()
        return Response({"message": "Article deleted"}, status=status.HTTP_200_OK)