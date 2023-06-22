from django.test import TestCase
from django.utils import timezone
import datetime
from .models import Question


class QuestionModelTests(TestCase):
    def was_published_recently_with_future_questions(self):
        """Метод должен возвращать False для вопросов, у которых pub_date в будущем"""
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)
