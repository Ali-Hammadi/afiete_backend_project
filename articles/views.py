# Path: articles/views.py
from users.permissions import IsAccountActiveAndUnfrozen
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
    PatientArticleSerializer,  # استيراد السيريالايزر النظيف الجديد للمريض
    ReactionSerializer,
    DeleteArticleSerializer,
    ArticleUpdateSerializer
)
from .models import Article, Reaction
from .recommender import recommend_articles
from .pagination import ArticlePagination

class ArticleCreateAPIView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor, IsAccountActiveAndUnfrozen]
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
    serializer_class = PatientArticleSerializer # المريض عند جلب مقالة مفردة يرى بيانات نظيفة أيضاً
    
    def get_queryset(self):
        return Article.objects.with_reactions(user=self.request.user).filter(status="Approved")

class ArticleListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = ArticleSerializer # الطبيب يحتاج لرؤية التفاصيل الكاملة بما فيها الـ status لمقالاته
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
    serializer_class = PatientArticleSerializer # المريض يرى التوصيات بدون حقول إدارية زائدة
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
    serializer_class = PatientArticleSerializer # 🌟 تعديل أساسي: استخدام السيريالايزر النظيف للمريض والزوار
    pagination_class = ArticlePagination

    def get_queryset(self):
        # يضمن سحب المقالات المقبولة فقط ومرتبة من الأحدث للأقدم
        return Article.objects.with_reactions(user=self.request.user).filter(status="Approved").order_by('-created_at')

class ArticlesMostReactionScoreListAPIView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PatientArticleSerializer # التريند للمرضى يعرض مخرجات نظيفة
    pagination_class = ArticlePagination

    def get_queryset(self):
        return Article.objects.with_reactions(user=self.request.user).filter(status="Approved").order_by('-score', '-likes')

class ArticleUpdateAPIView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated, IsDoctor]
    serializer_class = ArticleUpdateSerializer
    lookup_field = 'pk'

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user.doctor)


class ReactionGenericAPIView(generics.GenericAPIView):
    # 🔥 التحصين الصارم: يسمح فقط للمستخدم المسجل والـ Patient بالتفاعل
    permission_classes = [permissions.IsAuthenticated, IsPatient, IsAccountActiveAndUnfrozen]
    serializer_class = ReactionSerializer

    def post(self, request, article_id):
        user = request.user
        article = get_object_or_404(Article, id=article_id)
        
        # التأكد من أن المقالة مقبولة أولاً لكي يتم التفاعل معها
        if article.status != 'Approved':
            return Response({"error": "Article not approved"}, status=status.HTTP_400_BAD_REQUEST)
            
        reaction_type = request.data.get('reaction')
        if reaction_type not in [Reaction.LIKE, Reaction.DISLIKE]:
            return Response({"error": "Invalid reaction type"}, status=status.HTTP_400_BAD_REQUEST)
        
        exist = Reaction.objects.filter(user=user, article=article).first()
        if exist:
            # إذا ضغط المستخدم على نفس التفاعل مجدداً، يتم حذفه (Toggle)
            if exist.reaction == reaction_type:
                exist.delete()
                return Response({"message": f"{reaction_type} removed"}, status=status.HTTP_200_OK)
            else:
                # إذا غيّر رأيه من Like إلى Dislike أو العكس، يتم التحديث
                exist.reaction = reaction_type
                exist.save()
                return Response({"message": f"{reaction_type} updated"}, status=status.HTTP_200_OK)
        
        # إنشاء تفاعل جديد في حال لم يكن هناك تفاعل سابق
        Reaction.objects.create(user=user, article=article, reaction=reaction_type)
        return Response({"message": f"{reaction_type} added"}, status=status.HTTP_201_CREATED)


class DeleteArticleGenericAPIView(generics.GenericAPIView):
    serializer_class = DeleteArticleSerializer
    permission_classes = [permissions.IsAuthenticated, IsDoctor, IsAccountActiveAndUnfrozen]

    def delete(self, request, article_id):
        article = get_object_or_404(Article, id=article_id)
        if article.author != request.user.doctor:
            return Response({"error": "Article not related to author"}, status=status.HTTP_400_BAD_REQUEST)
        
        article.delete()
        return Response({"message": "Article deleted"}, status=status.HTTP_200_OK)