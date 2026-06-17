from django.contrib import admin
from django.core.exceptions import PermissionDenied
from .models import Note

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'creator', 'shared_with', 'note_type', 'is_shared', 'created_at']
    list_filter = ['note_type', 'is_shared', 'created_at']
    search_fields = ['content', 'creator__username', 'shared_with__username']
    
    def get_queryset(self, request):
        """
        Strictly restricts the admin view to only show shared notes.
        Private/personal notes are completely hidden from the admin panel.
        """
        qs = super().get_queryset(request)
        return qs.filter(is_shared=True)

    def has_change_permission(self, request, obj=None):
        """ Prevents modification of notes from the admin panel """
        return False

    def has_view_permission(self, request, obj=None):
        """ Denies viewing the individual object if it is private """
        if obj and not obj.is_shared:
            return False
        return True