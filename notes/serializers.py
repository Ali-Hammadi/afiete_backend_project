from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from .models import Note
# Import your Appointment & TreatmentCourse models here
# from clinic.models import Appointment, TreatmentCourse

# --- Your Appointment Serializer (English Cleaned) ---
class PatientUpdateNextSessionSerializer(serializers.ModelSerializer):
    class Meta:
        # model = Appointment
        fields = ['has_next_session']

    def validate(self, attrs):
        if self.instance.status not in ['Completed', 'Missed']: # Adjusted to match your choice strings/enums
            raise ValidationError("You can only update the next session status for completed or missed appointments.")
        return attrs


# --- Notes Serializers ---
class NoteSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='creator.get_full_name', read_only=True)
    is_course_ended = serializers.SerializerMethodField()

    class Meta:
        model = Note
        fields = ['id', 'content', 'note_type', 'is_shared', 'created_at', 'doctor_name', 'is_course_ended', 'shared_with']
        read_only_fields = ['creator', 'created_at']

    def get_is_course_ended(self, obj):
        if not obj.is_shared or not obj.shared_with:
            return False
        # Inject your actual course logic here if needed
        return False

    def validate(self, attrs):
        request = self.context.get('request')
        user = request.user
        
        is_shared = attrs.get('is_shared', self.instance.is_shared if self.instance else False)
        note_type = attrs.get('note_type', self.instance.note_type if self.instance else 'PERSONAL')
        shared_with = attrs.get('shared_with', self.instance.shared_with if self.instance else None)

        if note_type == 'SESSION' or (is_shared and shared_with):
            # Example check to enforce active course boundaries
            # if course and course.is_ended:
            #     raise ValidationError("Action denied. Cannot create or share notes after the treatment course has ended.")
            pass

        return attrs