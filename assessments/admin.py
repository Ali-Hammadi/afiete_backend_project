from django.contrib import admin
from .models import QuestionGroup, Question, AnswerOption, UserAnswer

Models = [
    QuestionGroup, 
    Question,
    AnswerOption,
    UserAnswer,
]

admin.site.register(Models)