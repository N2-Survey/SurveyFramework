import unittest
import warnings

import pandas as pd
from pandas._testing import assert_frame_equal, assert_series_equal

from n2survey.lime import LimeSurvey


class BaseTestCase(unittest.TestCase):
    """Base TestCase"""

    def assert_df_equal(self, df1, df2, msg):
        """DataFrame equality test from pandas"""
        try:
            assert_frame_equal(df1, df2)
        except AssertionError:
            raise self.failureException(msg)

    def assert_series_equal(self, s1, s2, msg):
        """Series equality test from pandas"""
        try:
            assert_series_equal(s1, s2)
        except AssertionError:
            raise self.failureException(msg)

    def setUp(self) -> None:
        self.addTypeEqualityFunc(pd.DataFrame, self.assert_df_equal)
        self.addTypeEqualityFunc(pd.Series, self.assert_series_equal)


class BaseTestLimeSurvey2021Case(BaseTestCase):
    """Base TestCase for testing survey files parsing using 2021 dummy"""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.structure_file = "data/survey_structure_2021.xml"
        cls.responses_file = "data/dummy_data_2021_codeonly.csv"
        # Default test questions
        cls.single_choice_column = "A6"
        cls.multiple_choice_column = "C3"
        cls.array_column = "B6"
        cls.free_column = "B12"
        # Read lime survey
        cls.survey = LimeSurvey(structure_file=cls.structure_file)


class BaseTestLimeSurvey2021WithResponsesCase(BaseTestLimeSurvey2021Case):
    """Base TestCase for testing survey files parsing using 2021 dummy"""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Read responses
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            cls.survey.read_responses(responses_file=cls.responses_file)
