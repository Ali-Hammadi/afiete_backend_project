# Path: articles/models.py

from django.db import models
from django.conf import settings
from doctors.models import Doctor, SubSpecialization
from .managers import ArticleManager

class Article(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected")
    ]
    
    objects = ArticleManager()
    
    author = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')
    title = models.CharField(max_length=255)
    content = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)  # يسجل وقت الإنشاء فقط
    updated_at = models.DateTimeField(auto_now=True)      # يتحدث عند كل تعديل

    specialization = models.ForeignKey(
        SubSpecialization,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='articles'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        author_name = self.author.user.username if self.author and self.author.user else "Unknown"
        return f"{self.title} by {author_name}"


class Reaction(models.Model):
    LIKE    = 'like'
    DISLIKE = 'dislike'

    REACTION_CHOICES = [
        (LIKE,    'Like'),
        (DISLIKE, 'Dislike'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    
    class Meta: 
        unique_together = ['article', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.reaction} - {self.article.title}"