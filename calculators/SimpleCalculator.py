"""
File that contains the SimpleCalculator class that represents a calculator which scores records.
"""
from core.answers import OpenRecord, TestRecord
from core.routes import PointsCalculator


# noinspection Style,Annotator
class SimpleCalculator(PointsCalculator):
    """
    Represents a calculator for scoring answers.

    This calculator extends the PointsCalculator class and implements
    specific scoring methods for open and test questions.

    """

    def __init__(self):
        """
        Initializes a SimpleCalculator object.
        """
        super().__init__()

    def score_open(self, record: OpenRecord) -> float:
        """
        Scores an open question record.

        :param record: (:class:`OpenRecord`) The open question record to score.
        :return: (:class:`float`) The score for the open question.
        """
        return 0.5

    def score_test(self, record: TestRecord) -> float:
        """
        Scores a test question record.

        :param record: (:class:`TestRecord`) The test question record to score.
        :return: (:class:`float`) The score for the test question.
        """
        if record.question.answer == record.person_answer:
            return 1
        return 0
