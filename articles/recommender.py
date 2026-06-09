# Path: articles/recommender.py

from django.db.models import Max, Sum
from .models import Article
from assessments.models import UserAnswer, AnswerOption

def recommend_articles(patient, top_n: int = 5) -> list:
    # 1. حساب السكورات لكل QuestionGroup بناءً على إجابات المريض
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
            group_data[group.id] = {"name": group.name, "raw": 0, "max": max_score}
        group_data[group.id]["raw"] += ua.answer_option.score

    scores = {
        gid: {"name": data["name"], "score": round((data["raw"] / data["max"]) * 100, 1)}
        for gid, data in group_data.items()
    }
    
    # ترتيب المجموعات الصحية تنازلياً حسب الأعلى سكور (الأكثر احتياجاً للتوصية)
    ranked = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)

    # 2. تجميع الـ IDs للمقالات بناءً على الترتيب التصاعدي/التنازلي للمجموعات دون تكرار
    recommended_ids = []
    seen_ids = set()

    for group_id, info in ranked:
        articles = Article.objects.filter(
            status="Approved",
            specialization__question_group_id=group_id
        ).values_list('id', flat=True)
        
        for article_id in articles:
            if article_id not in seen_ids:
                seen_ids.add(article_id)
                recommended_ids.append(article_id)
                
    return recommended_ids[:top_n]