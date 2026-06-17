from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

class Note(models.Model):
    NOTE_TYPE_CHOICES = [
        ('SESSION', 'Session Note'),
        ('PERSONAL', 'Personal Note'),
    ]

    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='created_notes'
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='shared_notes'
    )
    content = models.TextField()
    note_type = models.CharField(max_length=10, choices=NOTE_TYPE_CHOICES, default='PERSONAL')
    is_shared = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Note #{self.id} by {self.creator.username}"

    def save(self, *args, **kwargs):
        # Strict rule: If the note was already shared, deny any content updates (Static text)
        if self.pk:
            original = Note.objects.get(pk=self.pk)
            if original.is_shared:
                raise ValidationError("This note has already been shared and its content cannot be modified.")
        
        super().save(*args, **kwargs)