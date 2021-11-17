"""Test functions related to plot functions"""
import unittest

import pandas as pd

from n2survey.plot import plot_multiple_choice
from tests.common import BaseTestLimeSurvey2021Case


class TestMultipleChoicePlots(BaseTestLimeSurvey2021Case):
    """Test plots for multiple choice questions"""

    def get_responses_counts_temp(self):
        """Temporary replacement function for get_responses_counts method"""

        columns = list(self.survey.get_question(self.multiple_choice_column).index)[:-1]
        raw_data = self.survey.responses[columns]
        response_raw = raw_data.notnull()
        response_counts = pd.DataFrame(response_raw.sum(axis=0))
        response_counts = response_counts.rename(columns={0: "counts"})
        total_response = response_raw.shape[0]
        response_counts["percentage"] = response_counts["counts"] / total_response * 100

        return response_counts

    def test_bar_plot(self):
        """Test bar plot"""

        # To be replaced by output of get_responses_counts method when available
        data_df = self.get_responses_counts_temp()

        question_label = self.survey.get_label(self.multiple_choice_column)

        question_choices = self.survey.get_choices(self.multiple_choice_column)

        plot_multiple_choice.make_bar_plot_for_multiple_choice_question(
            data_df,
            question_label,
            question_choices,
            display_title=True,
            bar_spacing=1.2,
        )


if __name__ == "__main__":
    unittest.main()
