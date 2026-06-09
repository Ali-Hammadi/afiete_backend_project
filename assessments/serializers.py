from rest_framework import serializers
from .models import QuestionGroup, Question, AnswerOption, UserAnswer
from rest_framework.response import Response
from django.db import transaction
from .scoring import calculate_scores

class AnswerOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerOption
        fields = '__all__'

class QuestionSerializer(serializers.ModelSerializer):
    options = AnswerOptionSerializer(many=True, read_only=True)
    class Meta:
        model = Question  
        fields = ['id', 'text', 'order', 'options']
    

class ServeyFormSerializer(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True, read_only=True)
    class Meta:
        model = QuestionGroup
        fields = ['id', 'name', 'description', 'order', 'questions']

class UserAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer_id = serializers.IntegerField()

class SubmitAnswerSerializer(serializers.ModelSerializer):
    answers = UserAnswerSerializer(many=True)

    class Meta: 
        model = UserAnswer
        fields = ['answers']
    def create(self, validated_data):
        request = self.context['request']
        patient = request.user.patient
    
        answers_data = validated_data.get('answers', [])
    
        try:
            with transaction.atomic():
                for item in answers_data:
                    question_id = item.get('question_id')
                    answer_id   = item.get('answer_id')
    
                    answer_option = AnswerOption.objects.get(id=answer_id)
    
                    if answer_option.question_id != question_id:
                        raise serializers.ValidationError(
                            f"Answer option {answer_id} does not belong to question {question_id}."
                        )
    
                    UserAnswer.objects.update_or_create(
                        patient=patient,
                        question_id=question_id,
                        defaults={'answer_option': answer_option}
                    )
    
        except serializers.ValidationError:
            raise
        except Exception as e:
            raise serializers.ValidationError(str(e))
    
        return request.data


"""
{
    "answers": [{
           "question_id":1,
           "answer_id":2}
]
}

"""

# questionnaire/serializers.py

class ScoresSerializer(serializers.Serializer):

    def to_representation(self, patient):
        from django.db.models import Max, Sum
        from .models import UserAnswer, AnswerOption

        answers = (
            UserAnswer.objects
            .filter(patient=patient)
            .select_related('answer_option__question__questiongroup')
        )

        group_data = {}

        for ua in answers:
            group = ua.answer_option.question.questiongroup

            if group.id not in group_data:
                max_score = (
                    AnswerOption.objects
                    .filter(question__questiongroup=group)
                    .values('question_id')
                    .annotate(max_q=Max('score'))
                    .aggregate(total=Sum('max_q'))['total'] or 1
                )
                group_data[group.id] = {
                    "name": group.name,
                    "raw":  0,
                    "max":  max_score,
                }

            group_data[group.id]["raw"] += ua.answer_option.score

        return {
            data["name"]: {
                "score":    round((data["raw"] / data["max"]) * 100, 1),
                "raw":      data["raw"],
                "max":      data["max"],
                "severity": self._severity(data["raw"] / data["max"]),
            }
            for data in group_data.values()
        }

    @staticmethod
    def _severity(ratio: float) -> str:
        if ratio >= 0.75: return "severe"
        if ratio >= 0.50: return "moderate"
        if ratio >= 0.25: return "mild"
        return "minimal"

