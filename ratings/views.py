from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .serializers import RatingSerializer, RatingReadSerializer
from .models import Rating
from .pagination import RatingPagination

from users.permissions import IsPatient
from appointments.models import Appointment

from users.utils import is_doctor
class RatingCreateView(generics.CreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated, IsPatient]
    
    def perform_create(self, serializer):

        serializer.save()

class RatingListView(generics.ListAPIView):
    serializer_class = RatingReadSerializer
    pagination_class = RatingPagination
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        doctor_username = self.kwargs.get('doctor_username')

        # المراجعات للطبيب نفسه
        if not doctor_username and is_doctor(self.request.user):
            print(self.request.user.username)
            return Rating.objects.filter(
                appointment__doctor = self.request.user.doctor
            )
        
        # المراجعات للطبيب حسب username
        return Rating.objects.filter(
            appointment__doctor__user__username=doctor_username
        ).select_related('appointment__patient__user').order_by('-created_at')