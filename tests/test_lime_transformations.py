"""Test functions related to Transformations functions"""
import unittest

import pandas as pd

from n2survey.lime.transformations import (
    calculate_phd_duration,
    rate_mental_health,
    rate_supervision,
)
from tests.common import BaseTestLimeSurvey2021WithResponsesCase


class TestRateMentalHealth(BaseTestLimeSurvey2021WithResponsesCase):
    """Test Transformations rate_mental_health"""

    def test_state_anxiety(self):
        """Test rating state anxiety"""
        question = "D1"
        result = rate_mental_health(
            question_label=self.survey.get_label(question + "_SQ001"),
            responses=self.survey.get_responses(question, labels=False),
            choices=self.survey.get_choices(question),
        )

        ref = pd.DataFrame(
            data={
                "state_anxiety_score": [50.0, 100 / 3, 130 / 3],
                "state_anxiety_class": pd.Categorical(
                    ["A3", "A1", "A2"],
                    categories=[
                        "A1",
                        "A2",
                        "A3",
                    ],
                    ordered=True,
                ),
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"

        self.assert_df_equal(result.iloc[:3, -2:], ref, msg="DataFrames not equal.")

    def test_trait_anxiety(self):
        """Test rating trait anxiety"""

        question = "D2"
        result = rate_mental_health(
            question_label=self.survey.get_label(question + "_SQ001"),
            responses=self.survey.get_responses(question, labels=False),
            choices=self.survey.get_choices(question),
        )

        ref = pd.DataFrame(
            data={
                "trait_anxiety_score": [47.5, 32.5, 50.0],
                "trait_anxiety_class": pd.Categorical(
                    ["A3", "A1", "A3"],
                    categories=[
                        "A1",
                        "A2",
                        "A3",
                    ],
                    ordered=True,
                ),
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"

        self.assert_df_equal(result.iloc[:3, -2:], ref, msg="DataFrames not equal.")

    def test_depression(self):
        """Test rating depression"""

        question = "D3"
        result = rate_mental_health(
            question_label=self.survey.get_label(question + "_SQ001"),
            responses=self.survey.get_responses(question, labels=False),
            choices=self.survey.get_choices(question),
        )

        ref = pd.DataFrame(
            data={
                "depression_score": [8.0, 5.0, 8.0],
                "depression_class": pd.Categorical(
                    ["A2", "A2", "A2"],
                    categories=[
                        "A1",
                        "A2",
                        "A3",
                        "A4",
                        "A5",
                    ],
                    ordered=True,
                ),
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"

        self.assert_df_equal(result.iloc[:3, -2:], ref, msg="DataFrames not equal.")


class TestRateSupervision(BaseTestLimeSurvey2021WithResponsesCase):
    """Test Transformations rate_supervision for formal and direct supervision"""

    def test_formal_supervision(self):
        """Test rating of formal supervision"""

        question = "E7a"
        result = rate_supervision(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question, labels=False),
            choices=self.survey.get_choices(question),
        )

        ref = pd.DataFrame(
            data={
                "formal_supervision_score": [4.0, 5.0, 1.0],
                "formal_supervision_class": pd.Categorical(
                    ["A2", "A1", "A5"],
                    categories=[
                        "A1",
                        "A2",
                        "A3",
                        "A4",
                        "A5",
                    ],
                    ordered=True,
                ),
            },
            index=[8, 9, 10],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[6:9, -2:], ref, msg="DataFrames not equal.")

    def test_direct_supervision(self):
        """Test rating of direct supervision"""

        question = "E7b"
        result = rate_supervision(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question, labels=False),
            choices=self.survey.get_choices(question),
        )
        ref = pd.DataFrame(
            data={
                "direct_supervision_score": [4.0, 5.0, 1.0],
                "direct_supervision_class": pd.Categorical(
                    ["A2", "A1", "A5"],
                    categories=[
                        "A1",
                        "A2",
                        "A3",
                        "A4",
                        "A5",
                    ],
                    ordered=True,
                ),
            },
            index=[8, 9, 10],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[6:9, -2:], ref, msg="DataFrames not equal.")


class TestPhDDuration(BaseTestLimeSurvey2021WithResponsesCase):
    """Test Transformations calculate_phd_duration"""

    def test_phd_duration(self):
        """Test calculated phd duration"""

        start_question = "A8"
        end_question = "A9"
        # phd_duration_questions = {"phd_duration": ("A8", "A9")}

        result = calculate_phd_duration(
            start_responses=self.survey.get_responses(start_question, labels=False),
            end_responses=self.survey.get_responses(end_question, labels=False),
        )
        # survey = LimeSurvey(structure_file=self.structure_file)
        # survey.read_responses(
        #     responses_file=self.responses_file,
        #     transformation_questions=phd_duration_questions,
        # )
        ref = pd.DataFrame(
            data={
                "PhD duration (days)": [1826.0, 1095.0, 1065.0],
                "PhD duration (months)": [60.0, 36.0, 35.0],
                "PhD duration (years)": [5.0, 3.0, 3.0],
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, :], ref, msg="DataFrames not equal.")


if __name__ == "__main__":
    unittest.main()
