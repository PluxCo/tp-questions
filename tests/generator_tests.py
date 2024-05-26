import datetime
import time
from unittest import TestCase

# noinspection PyUnresolvedReferences
from core import answers, questions
from core.answers import Record, AnswerState
from core.questions import TestQuestion, QuestionGroupAssociation
from db_connector import DBWorker
from generator.generators import SmartGenerator
from users import Person


class SmartGenerationTestCase(TestCase):
    def setUp(self):
        # Initialize the in-memory database and populate it with test data
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session
        for i in range(25):
            question = TestQuestion(id=i + 1,
                                    text=f'Sample Question {i}',
                                    subject='Sample Subject',
                                    options=["option 1", "option 2", "option 3", "option 4"],
                                    answer='1',
                                    level=i % 5 + 1,
                                    article_url='https://example.com')
            self.session.add(question)
            question_group = QuestionGroupAssociation(question_id=question.id, group_id=f'test {i % 2 + 1}')
            self.session.add(question_group)
        self.session.commit()

    def tearDown(self):
        # Close the session after each test
        self.session.close()

    def test_question_coverage(self):
        # Check that the generator covers all questions
        person = Person(user_id='user', groups=[('test 1', 2), ('test 2', 2)])
        questions_asked = {}
        for i in range(25):
            question = SmartGenerator().next_bunch(person=person)[0]
            if questions_asked.get(question.id) is not None:
                questions_asked[question.id] += 1
            else:
                questions_asked[question.id] = 1
            answer = Record(type='TEST', question_id=question.id, person_answer='1', person_id=person.id,
                            ask_time=datetime.datetime.now(), answer_time=datetime.datetime.now(),
                            state=AnswerState.ANSWERED, points=1 if i < 12 else 0)
            self.session.add(answer)
            self.session.commit()

        # Ensure that each question was asked exactly once
        self.assertEqual(25, len(questions_asked))
        print(questions_asked)

    def test_question_group_coverage(self):
        # Check that the generator covers all questions from a specific group
        person = Person(user_id='user', groups=[('test 1', 2)])
        questions_asked = {}
        for i in range(12):
            question = SmartGenerator().next_bunch(person=person)[0]
            if questions_asked.get(question.id) is not None:
                questions_asked[question.id] += 1
            else:
                questions_asked[question.id] = 1
            answer = Record(type='TEST', question_id=question.id, person_answer='1', person_id=person.id,
                            ask_time=datetime.datetime.now(), answer_time=datetime.datetime.now(),
                            state=AnswerState.ANSWERED, points=1)
            self.session.add(answer)
            self.session.commit()

        # Ensure that each question from the group was asked exactly once
        self.assertEqual(12, len(questions_asked))

    def test_question_level_distribution(self):
        # Check that the generator correctly distributes question levels
        person = Person(user_id='user', groups=[('test 1', 2), ('test 2', 2)])
        levels_asked = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for i in range(100):
            question = SmartGenerator().next_bunch(person=person)[0]
            levels_asked[question.level] += 1
            answer = Record(type='TEST', question_id=question.id, person_answer='1', person_id=person.id,
                            ask_time=datetime.datetime.now(), answer_time=datetime.datetime.now(),
                            state=AnswerState.ANSWERED, points=1)
            self.session.add(answer)
            self.session.commit()

        # Check that level 2 was asked the most and level 5 the least
        self.assertEqual(2, max(levels_asked, key=levels_asked.get))
        self.assertEqual(5, min(levels_asked, key=levels_asked.get))

        # Check that the number of questions for levels 1 and 2 is approximately the same
        self.assertAlmostEqual(levels_asked[1], levels_asked[2], delta=10)

    def test_question_distribution_based_on_points(self):
        # Check that the generator adjusts question difficulty based on points scored
        person = Person(user_id='user', groups=[('test 1', 2), ('test 2', 2)])
        questions_asked = []

        for i in range(500):
            question = SmartGenerator().next_bunch(person=person)[0]
            questions_asked.append(question)

            # High points for the first 250 questions
            if i < 250:
                points = 1
            # Low points for the next 250 questions
            else:
                points = 0

            answer = Record(type='TEST', question_id=question.id, person_answer='1', person_id=person.id,
                            ask_time=datetime.datetime.now(), answer_time=datetime.datetime.now(),
                            state=AnswerState.ANSWERED, points=points)
            self.session.add(answer)
            self.session.commit()

        # Check question levels for high and low points
        high_points_responses = questions_asked[:250]
        low_points_responses = questions_asked[250:]

        high_points_levels = [q.level for q in high_points_responses]
        low_points_levels = [q.level for q in low_points_responses]

        # Verify that the total level of questions for high points is greater than or equal to
        # the total level of questions for low points
        self.assertGreaterEqual(sum(high_points_levels), sum(low_points_levels))
        print("The gap between levels of high_points and low_points answers:",
              sum(high_points_levels) / 250 - sum(low_points_levels) / 250)

    def test_incorrect_answers_asked_more_frequently(self):
        person = Person(user_id='user', groups=[('test 1', 2), ('test 2', 2)])
        incorrect_questions = set()
        correct_questions = set()

        # Answering questions
        for i in range(25):
            question = SmartGenerator().next_bunch(person=person)[0]

            if i < 12:
                # Incorrect answers for the first 12 questions
                points = 0
                incorrect_questions.add(question.id)
            else:
                # Correct answers for the next questions
                points = 1
                correct_questions.add(question.id)

            answer = Record(type='TEST', question_id=question.id, person_answer='1', person_id=person.id,
                            ask_time=datetime.datetime.now(), answer_time=datetime.datetime.now(),
                            state=AnswerState.ANSWERED, points=points)
            self.session.add(answer)
            self.session.commit()

        asked_questions = []

        # Asking 50 more questions
        for i in range(50):
            question = SmartGenerator().next_bunch(person=person)[0]
            asked_questions.append(question.id)
            answer = Record(type='TEST', question_id=question.id, person_answer='1', person_id=person.id,
                            ask_time=datetime.datetime.now(), answer_time=datetime.datetime.now(),
                            state=AnswerState.ANSWERED, points=1)
            self.session.add(answer)
            self.session.commit()

        # Count how many times each question was asked
        incorrect_question_asked_count = sum(1 for q_id in asked_questions if q_id in incorrect_questions)
        correct_question_asked_count = sum(1 for q_id in asked_questions if q_id in correct_questions)

        # Ensure that incorrect questions are asked more frequently than correct ones
        print(incorrect_question_asked_count, correct_question_asked_count)
        self.assertGreater(incorrect_question_asked_count, correct_question_asked_count)

    def test_no_questions_available(self):
        # Initialize an empty database
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session

        person = Person(user_id='user', groups=[('test 1', 2)])

        # Try to generate a question when there are no questions available
        question = SmartGenerator().next_bunch(person=person)

        # Ensure no questions are returned
        self.assertEqual(0,len(question))

    def test_performance_large_database(self):
        # Populate the database with a large number of questions
        DBWorker.init_db_file("sqlite:///:memory:", force=True)
        self.session = DBWorker().session
        for i in range(10_000):
            question = TestQuestion(id=i + 1,
                                    text=f'Sample Question {i}',
                                    subject='Sample Subject',
                                    options=["option 1", "option 2", "option 3", "option 4"],
                                    answer='1',
                                    level=i % 5 + 1,
                                    article_url='https://example.com')
            self.session.add(question)
            question_group = QuestionGroupAssociation(question_id=question.id, group_id=f'test {i % 2 + 1}')
            self.session.add(question_group)
        self.session.commit()

        person = Person(user_id='user', groups=[('test 1', 2), ('test 2', 3)])

        start_time = time.perf_counter_ns()
        SmartGenerator().next_bunch(person=person)
        end_time = time.perf_counter_ns()

        # Ensure the operation completes within a reasonable time
        self.assertLess((end_time - start_time)/10**9, 1)
