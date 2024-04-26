import numpy as np
import torch
from torch.nn import functional
from transformers import AutoTokenizer, AutoModel

from core.answers import OpenRecord, TestRecord
from core.routes import PointsCalculator


class SmartCalculator(PointsCalculator):
    """
    Represents a calculator for scoring answers.

    This calculator extends the PointsCalculator class and implements
    specific scoring methods for open and test questions. It uses sentence
    transformers for scoring open answers.

    """

    def __init__(self, metrics=np.dot):
        """
        Initializes a SmartCalculator object.
        :param metrics: The metrics method to use for scoring.
        """
        super().__init__()
        self.tokenizer = AutoTokenizer.from_pretrained('tokenizer')
        self.model = AutoModel.from_pretrained('model')
        self.metrics = metrics

    @staticmethod
    def _mean_pooling(model_output, attention_mask) -> torch.Tensor:
        """
        Mean Pooling – Take attention mask into account for correct averaging
        :param attention_mask: The attention mask to apply
        :return: The averaged result
        """
        token_embeddings = model_output[0]  # First element of model_output contains all token embeddings
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()

        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)

    def score_open(self, record: OpenRecord) -> float:
        """
        Scores an open question record.

        :param record: (:class:`OpenRecord`) The open question record to score.
        :return: (:class:`float`) The score for the open question.
        """

        encoded_input = self.tokenizer([record.question.answer, record.person_answer], padding=True, truncation=True,
                                       return_tensors='pt')
        # Compute token embeddings
        with torch.no_grad():
            model_output = self.model(**encoded_input)

        # Perform pooling
        answer_relation = self._mean_pooling(model_output, encoded_input['attention_mask'])

        # Normalize embeddings
        answer_relation = functional.normalize(answer_relation, p=2)

        # Find the similarity
        score = self.metrics(*answer_relation)

        return float(score)

    def score_test(self, record: TestRecord) -> float:
        """
        Scores a test question record.

        :param record: (:class:`TestRecord`) The test question record to score.
        :return: (:class:`float`) The score for the test question.
        """
        if record.question.answer == record.person_answer:
            return 1
        return 0
