"""Test functions related to plot functions"""
import unittest

from n2survey.plot import plot_multiple_choice
from tests.common import BaseTestLimeSurvey2021Case


class TestMultipleChoicePlots(BaseTestLimeSurvey2021Case):
    """Test plots for multiple choice questions"""

    def test_bar_plot(self):
        """Test bar plot"""

        data_df = self.survey.count(
            self.multiple_choice_column, labels=True, add_totals=True, percents=True
        )

        plot_multiple_choice.make_bar_plot_for_multiple_choice_question(
            data_df,
            sort="descending",
            display_title=True,
            bar_spacing=1.2,
        )


if __name__ == "__main__":
    unittest.main()
