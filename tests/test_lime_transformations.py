"""Test functions related to Transformations functions"""
import unittest

import numpy as np
import pandas as pd

from n2survey.lime.transformations import (
    calculate_duration,
    range_to_numerical,
    rate_mental_health,
    rate_satisfaction,
    rate_supervision,
    rate_satisfaction,
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
                "state_anxiety_score": [
                    50.0,
                    100 / 3,
                    130 / 3,
                    48.0,
                    np.nan,
                    np.nan,
                    60.0,
                ],
                "state_anxiety_class": pd.Categorical(
                    ["A3", "A1", "A2", "A3", np.nan, np.nan, "A3"],
                    categories=[
                        "A1",
                        "A2",
                        "A3",
                    ],
                    ordered=True,
                ),
            },
            index=[2, 3, 4, 24, 28, 30, 46],
        )
        ref.index.name = "id"

        self.assert_df_equal(
            result.iloc[[0, 1, 2, 19, 21, 22, 34], -2:],
            ref,
            msg="DataFrames not equal.",
        )

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
                "trait_anxiety_score": [
                    47.5,
                    32.5,
                    50.0,
                    55.0,
                    170 / 3,
                    np.nan,
                    np.nan,
                ],
                "trait_anxiety_class": pd.Categorical(
                    ["A3", "A1", "A3", "A3", "A3", np.nan, np.nan],
                    categories=[
                        "A1",
                        "A2",
                        "A3",
                    ],
                    ordered=True,
                ),
            },
            index=[2, 3, 4, 24, 28, 46, 47],
        )
        ref.index.name = "id"

        self.assert_df_equal(
            result.iloc[[0, 1, 2, 19, 21, 34, 35], -2:],
            ref,
            msg="DataFrames not equal.",
        )

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
                "depression_score": [8.0, 5.0, 8.0, 10.0, 52 / 3, np.nan, np.nan],
                "depression_class": pd.Categorical(
                    ["A2", "A2", "A2", "A3", "A4", np.nan, np.nan],
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
            index=[2, 3, 4, 30, 43, 46, 47],
        )
        ref.index.name = "id"

        self.assert_df_equal(
            result.iloc[[0, 1, 2, 22, 31, 34, 35], -2:],
            ref,
            msg="DataFrames not equal.",
        )


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


class TestDuration(BaseTestLimeSurvey2021WithResponsesCase):
    """Test Transformation calculate_duration"""

    def test_phd_duration(self):
        """Test calculate_duration"""

        start_question = "A8"
        end_question = "A9"

        result = calculate_duration(
            start_responses=self.survey.get_responses(start_question, labels=False),
            end_responses=self.survey.get_responses(end_question, labels=False),
        )

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


class TestRangeToNumerical(BaseTestLimeSurvey2021WithResponsesCase):
    """Test Transformations range for different questions"""

    def test_range_to_numerical_noincome_duration(self):
        """Test convert to numerical noincome_duration"""

        question = "B1b"

        result = range_to_numerical(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question),
        )

        ref = pd.DataFrame(
            data={
                "noincome_duration": [np.NaN, np.NaN, np.NaN],
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -1:], ref, msg="DataFrames not equal.")

    def test_range_to_numerical_income_amount(self):
        """Test convert to numerical income_amount"""

        question = "B2"

        result = range_to_numerical(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question),
        )

        ref = pd.DataFrame(
            data={
                "income_amount": [1650.0, 1950.0, 2050.0],
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -1:], ref, msg="DataFrames not equal.")

    def test_range_to_numerical_costs_amount(self):
        """Test convert to numerical costs_amount"""

        question = "B3"

        result = range_to_numerical(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question),
        )

        ref = pd.DataFrame(
            data={
                "costs_amount": [850.0, 750.0, 550.0],
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -1:], ref, msg="DataFrames not equal.")

    def test_range_to_numerical_contract_duration(self):
        """Test convert to numerical contract_duration"""

        question = "B4"

        result = range_to_numerical(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question),
        )

        ref = pd.DataFrame(
            data={"contract_duration": [30.0, 48.0, 30.0]},
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -1:], ref, msg="DataFrames not equal.")

    def test_range_to_numerical_holiday_amount(self):
        """Test convert to numerical holiday_amount"""

        question = "B10"

        result = range_to_numerical(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question),
        )

        ref = pd.DataFrame(
            data={"holiday_amount": [28.0, 28.0, 28.0]},
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -1:], ref, msg="DataFrames not equal.")

    def test_range_to_numerical_hours_amount(self):
        """Test convert to numerical hours_amount"""

        question = "C4"

        result = range_to_numerical(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question),
        )

        ref = pd.DataFrame(
            data={"hours_amount": [53.0, 38.0, 43.0]},
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -1:], ref, msg="DataFrames not equal.")

    def test_range_to_numerical_holidaytaken_amount(self):
        """Test convert to numerical holidaytaken_amount"""

        question = "C8"

        result = range_to_numerical(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question),
        )

        ref = pd.DataFrame(
            data={"holidaytaken_amount": [8.0, 28.0, 13.0]},
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -1:], ref, msg="DataFrames not equal.")


class TestRateSatisfaction(BaseTestLimeSurvey2021WithResponsesCase):
    """Test Transformations rate_satisfaction for overall satisfaction"""

    def test_satisfaction(self):
        """Test rating of satisfaction"""

        question = "C1"
        result = rate_satisfaction(
            question_label=self.survey.get_label(question),
            responses=self.survey.get_responses(question, labels=False),
            choices=self.survey.get_choices(question),
        )
        ref = pd.DataFrame(
            data={
                "satisfaction_score": [5.0, 4.0, 3.0],
                "satisfaction_class": pd.Categorical(
                    ["A1", "A2", "A3"],
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
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(result.iloc[:3, -2:], ref, msg="DataFrames not equal.")


if __name__ == "__main__":
    unittest.main()
