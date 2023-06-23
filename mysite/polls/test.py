from django.test import TestCase
from django.utils import timezone
import datetime
from .models import Question, Choice
from django.urls import reverse
from http import HTTPStatus


def create_question(question_text, days):
    time = timezone.now() + datetime.timedelta(days=days)
    return Question.objects.create(question_text=question_text, pub_date=time)


def create_choice(question, choice_text=''):
    return Choice.objects.create(question=question, choice_text=choice_text)


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_questions(self):
        """Метод должен возвращать False для Questions, у которых pub_date в будущем."""
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """was_published_recently() возвращает True для вопросов, чья pub_date в пределах предыдущих суток."""
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


class QuestionIndexViewTests(TestCase):
    # def setUp(self):
    #     question = Question.objects.create()
    #     time = timezone.now() + datetime.timedelta(days=days)

    def test_no_questions(self):
        """При старте теста в базе нет Questions"""
        response = self.client.get(reverse("polls:index"))
        self.assertContains(response, "No polls are available.")
        self.assertEquals(response.status_code, 200)
        self.assertQuerySetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """Question c pub_date в прошлом присутствуют в queryset и отображаются на экране."""
        question = create_question('I am past question?', days=-1)
        create_choice(question=question)
        response = self.client.get(reverse("polls:index"))
        self.assertEquals(response.status_code, 200)
        self.assertQuerySetEqual(response.context['latest_question_list'], [question])

    def test_future_question(self):
        """Question c pub_date в прошлом отсутствуют в queryset и не отображаются на экране."""
        create_question('I am future question?', days=1)
        response = self.client.get(reverse("polls:index"))
        self.assertEquals(response.status_code, 200)
        self.assertQuerySetEqual(response.context['latest_question_list'], [])

    def test_past_and_future_question(self):
        """Question c pub_date в прошлом присутствуют в queryset, а с pub_date в будущем отсутствуют."""
        past_question = create_question('I am past question?', days=-1)
        choice = create_choice(past_question, 'choice for past q?')
        future_question = create_question('I am future question?', days=1)
        response = self.client.get(reverse("polls:index"))
        self.assertEquals(response.status_code, 200)
        self.assertQuerySetEqual(response.context['latest_question_list'], [past_question])

    def test_two_past_questions(self):
        """View index возвращает несколько questions с pub_date в прошлом."""
        question1 = create_question(question_text="Past question 1.", days=-30)
        question2 = create_question(question_text="Past question 2.", days=-5)
        choice1 = create_choice(question=question1)
        choice2 = create_choice(question=question2)
        response = self.client.get(reverse("polls:index"))
        self.assertQuerySetEqual(
            response.context["latest_question_list"],
            [question2, question1],
        )


class DetailViewTests(TestCase):

    def test_no_future_question(self):
        future_question = create_question('Future?', days=1)
        response = self.client.get(reverse('polls:detail', args={future_question.id}))
        self.assertEquals(response.status_code, HTTPStatus.NOT_FOUND)

    def test_no_future_question(self):
        past_question = create_question('Past?', days=-1)
        response = self.client.get(reverse('polls:detail', args={past_question.id}))
        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertContains(response, past_question.question_text)


class ResultsViewTests(TestCase):

    def test_no_future_question(self):
        future_question = create_question('Future?', days=1)
        response = self.client.get(reverse('polls:results', args={future_question.id}))
        self.assertEquals(response.status_code, HTTPStatus.NOT_FOUND)

    def test_no_future_question(self):
        past_question = create_question('Past?', days=-1)
        response = self.client.get(reverse('polls:results', args={past_question.id}))
        self.assertEquals(response.status_code, HTTPStatus.OK)
        self.assertContains(response, past_question.question_text)


class VoteTests(TestCase):

    def test_vote(self):
        question = create_question(question_text='', days=0)
        choice = create_choice(question=question, choice_text='choice for vote')
        self.assertEquals(choice.votes, 0)
        # response = self.client.post(f'/polls/{question.id}/vote', {"choice": {choice.id}})
        response = self.client.post(reverse('polls:vote', args={question.id}), data={"choice": choice.id})
        choice.refresh_from_db()
        self.assertEquals(response.status_code, 302)
        self.assertEquals(choice.votes, 1)

    def test_vote_not_select_choice(self):
        question = create_question(question_text='', days=0)
        choice = create_choice(question=question, choice_text='choice for vote')
        self.assertEquals(choice.votes, 0)
        response = self.client.post(reverse('polls:vote', args={question.id}))
        choice.refresh_from_db()
        self.assertEquals(response.status_code, 200)
        self.assertEquals(choice.votes, 0)
        self.assertEquals(response.context['error_message'], "You didn't select a choice.")

