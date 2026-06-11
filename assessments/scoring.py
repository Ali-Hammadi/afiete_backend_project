# questionnaire/scoring.py

from django.db.models import Max, Sum
from .models import UserAnswer, AnswerOption


def calculate_scores(patient) -> dict:
    """
    Returns: {"Depression": 75.0, "Anxiety": 50.0, ...}
    """
    answers = (
        UserAnswer.objects
        .filter(patient=patient)
        .select_related('answer_option__question__questiongroup')
    )
    print(answers)
    group_data = {}  # {group_id: {"name": str, "raw": float, "max": float}}

    for ua in answers:
        group = ua.answer_option.question.questiongroup

        if group.id not in group_data:
            # max ممكن لهاد الـ group = لكل سؤال خذ أعلى score وجمّعهم
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
        data["name"]: round((data["raw"] / data["max"]) * 100, 1)
        for data in group_data.values()
    }
