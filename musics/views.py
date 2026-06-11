from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from users.permissions import IsAccountActiveAndUnfrozen
from .models import MusicEntity, BreathingExerciseEntity, UserRelaxProfile
from .serializers import MusicEntitySerializer, BreathingExerciseEntitySerializer
from .recommendation import get_recommended_tracks
from drf_spectacular.utils import extend_schema
class LastFeelingView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]
    def get(self, request):
        profile, _ = UserRelaxProfile.objects.get_or_create(user=request.user)
        return Response({"last_selected_feeling": profile.last_selected_feeling})

    def post(self, request):
        feeling = request.data.get("feeling")
        profile, _ = UserRelaxProfile.objects.get_or_create(user=request.user)
        profile.last_selected_feeling = feeling
        profile.save()
        return Response({"status": "feeling saved successfully"})


class RecommendedTracksView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]

    def get(self, request):
        feeling = request.query_params.get("feeling")
        limit = int(request.query_params.get("limit", 5))
        exclude_id = request.query_params.get("excludeTrackId", None)

        if not feeling:
            # Fallback automatically to stored user feeling profile
            profile, _ = UserRelaxProfile.objects.get_or_create(user=request.user)
            feeling = profile.last_selected_feeling or "neutral"

        tracks = get_recommended_tracks(feeling, limit=limit, exclude_track_id=exclude_id)
        serializer = MusicEntitySerializer(tracks, many=True)
        return Response(serializer.data)


class BreathingExerciseListView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsAccountActiveAndUnfrozen]

    def get(self, request):
        exercises = BreathingExerciseEntity.objects.all()
        serializer = BreathingExerciseEntitySerializer(exercises, many=True)
        return Response(serializer.data)
