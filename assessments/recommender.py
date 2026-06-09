# doctors/recommender.py

from django.db.models import Max, Sum
from doctors.models import Doctor
from .models import UserAnswer, AnswerOption
from doctors.models import Doctor
# doctors/recommender.py

def recommend_doctors(patient, top_n: int = 5) -> list:

    # 1. احسب السكورات per QuestionGroup
    answers = (
        UserAnswer.objects
        .filter(patient=patient)
        .select_related('answer_option__question__questiongroup')
    )
    group_data = {}  # {group_id: {"name", "raw", "max"}}

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

    scores = {
        gid: {
            "name":  data["name"],
            "score": round((data["raw"] / data["max"]) * 100, 1),
        }
        for gid, data in group_data.items()
    }
    ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    # 2. رشّح عبر FK مباشرة — مش مطابقة نصية
    seen = {}

    for group_id, info in ranked:
        doctors = (
            Doctor.objects
            .filter(
                status='approved',
                specialties__question_group_id=group_id,  # ← FK مباشر
            )
            .select_related('user', 'job_title')
            .prefetch_related('specialties')
            .distinct().order_by('-experience')
        )

        for doctor in doctors:
            if doctor.id not in seen:
                seen[doctor.id] = {
                    "username":       doctor.user.username,
                    "name":           doctor.user.get_full_name(),
                    "job_title":      doctor.job_title.title if doctor.job_title else None,
                    'photo':          doctor.photo.url if doctor.photo else None,
                    "experience":     doctor.experience,
                    "primary_domain": info["name"], 
                    "primary_score":  info["score"],
                    "specialties":    [s.name for s in doctor.specialties.all()],
                }

    return sorted(seen.values(), key=lambda x: x["primary_score"], reverse=True)[:top_n]