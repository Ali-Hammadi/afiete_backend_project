from django.db import models
from doctors.models import Doctor, SubSpecialization
from users.models import User
from .managers import ArticleManager

class Article(models.Model):
    STATUS_CHOISES = [
        ("Pending","pending"),
        ("Approved","approved"),
        ("Rejected","rejected")
    ]
    objects = ArticleManager()
    author = models.ForeignKey(
        Doctor,
        on_delete= models.SET_NULL,
        null=True,
        blank=True
    )
    # status 
    status = models.CharField(max_length=15,choices=STATUS_CHOISES,default='pending')
    
    # content
    title = models.CharField(max_length=50)
    content = models.CharField(max_length=5000)

    # dates
    created_at = models.DateTimeField(auto_now=True)

    # specialization related this article
    specialization = models.ForeignKey(
        SubSpecialization,
        null= True,
        blank=True,
        on_delete=models.PROTECT
    )

    def __str__(self):
        return f"{self.title} by {self.author.user.username}"
class Reaction(models.Model):
    LIKE    = 'like'
    DISLIKE = 'dislike'

    REACTION_CHOICES = [
        (LIKE,    'Like'),
        (DISLIKE, 'Dislike'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    article = models.ForeignKey(
        Article, 
        on_delete=models.CASCADE,
        related_name='reactions'
    )
    reaction = models.CharField(max_length=10, choices=REACTION_CHOICES)
    
   
    class Meta: 
        unique_together = ['article', 'user']  # كل يوزر يقدر يعمل reaction واحد بس
    
    def __str__(self):
        return f"{self.user} - {self.reaction} - {self.article}"
