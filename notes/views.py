from rest_framework import viewsets, permissions
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db import models
from .models import Note
from .serializers import NoteSerializer

# 1. Admin Gateway ViewSet (Strictly Shared Notes Only)
class AdminNoteViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Dashboard API for the system Admin.
    Strictly filters and allows visibility ONLY for shared notes.
    """
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAdminUser] # Ensures only Staff/Admin can access

    def get_queryset(self):
        return Note.objects.filter(is_shared=True).order_by('-created_at')


# 2. Doctor Gateway ViewSet
class DoctorNoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Doctors see notes they created (Their personal notes + records written for their patients)
        return Note.objects.filter(creator=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


# 3. Patient Gateway ViewSet
class PatientNoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Patients see their own private notes + medical notes shared WITH them by doctors
        user = self.request.user
        return Note.objects.filter(
            models.Q(creator=user) | models.Q(shared_with=user, is_shared=True)
        ).order_by('-created_at')

    def perform_create(self, serializer):
        # If a patient creates a note, it defaults to a secure personal note
        serializer.save(creator=self.request.user, note_type='PERSONAL')
       
        
# 4. Shared Notes ViewSet (The Bridge)
class SharedNoteViewSet(viewsets.ReadOnlyModelViewSet):
    """ Shared endpoint where patients view notes shared BY doctors """
    serializer_class = NoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        # If patient: sees notes shared with them
        # If doctor: sees notes they have explicitly shared with patients
        return Note.objects.filter(
            models.Q(shared_with=user, is_shared=True) | 
            models.Q(creator=user, is_shared=True)
        ).order_by('-created_at')