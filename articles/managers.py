# managers.py

from django.db.models import Count, Q
from django.db import models
class ArticleManager(models.Manager):
    def with_reactions(self):
        return self.annotate(
            likes=Count('reactions', filter=Q(reactions__reaction='like')),
            dislikes=Count('reactions', filter=Q(reactions__reaction='dislike')),
            score=Count('reactions', filter=Q(reactions__reaction='like')) - 
                  Count('reactions', filter=Q(reactions__reaction='dislike'))
        ).order_by('-score', '-likes')