from django.contrib import admin
from .models import QuestionGroup, Question, AnswerOption, UserAnswer

# تسجيل الموديلات الخاصة بتطبيق الـ assessments في لوحة التحكم
Models = [
    QuestionGroup,
    Question,
    AnswerOption,
    UserAnswer
]

admin.site.register(Models)