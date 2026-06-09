# doctors/recommender.py

from django.db.models import Max, Sum
from assessments.models import UserAnswer, AnswerOption
from .models import Article

from django.db.models import Count, Q
# doctors/recommender.py

def recommend_articles(patient, top_n: int = 5) -> list:    

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
        articles = (
            Article.objects.with_reactions().filter(
                status = "Approved",
                specialization__question_group_id=group_id
            )
        )
        for article in articles: 
            if article.id not in seen: 
                seen[article.id] = {
                    "id":             article.id,
                }
        return seen