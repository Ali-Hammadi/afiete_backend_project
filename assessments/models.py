from django.db import models
from patients.models import Patient


class QuestionGroup(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if self.order is None:
            last_order = QuestionGroup.objects.aggregate(
                models.Max('order')
            )['order__max']
            self.order = (last_order or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Question(models.Model):
    questiongroup = models.ForeignKey(
        QuestionGroup,
        on_delete=models.CASCADE,
        related_name='questions'
    )
    text = models.TextField()
    order = models.PositiveBigIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if self.order is None:
            last_order = Question.objects.filter(
                questiongroup=self.questiongroup
            ).aggregate(models.Max('order'))['order__max']

            self.order = (last_order or 0) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return self.text


class AnswerOption(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options'
    )
    text = models.CharField(max_length=255)
    score = models.IntegerField()

    def __str__(self):
        return self.text


class UserAnswer(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='answers'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer_option = models.ForeignKey(AnswerOption, on_delete=models.CASCADE)

    class Meta:
        unique_together = ['patient', 'question']

    def clean(self):
        if self.answer_option.question_id != self.question_id:
            raise ValueError("Answer does not belong to the question")

    def __str__(self):
        return f"{self.patient} - {self.question}: {self.answer_option}"