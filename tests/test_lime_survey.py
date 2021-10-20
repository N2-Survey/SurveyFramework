"""Test functions related to Survey class"""
import unittest

import pandas as pd
from pandas._testing import assert_frame_equal

from n2survey.lime import LimeSurvey, read_lime_questionnaire_structure


class TestLimeSurveyInitialisation(unittest.TestCase):
    """Test LimeSurvey class initialisation"""

    def assert_df_equal(self, df1, df2, msg):
        """DataFrame equality test from pandas"""
        try:
            assert_frame_equal(df1, df2)
        except AssertionError:
            raise self.failureException(msg)

    def setUp(self):
        self.addTypeEqualityFunc(pd.DataFrame, self.assert_df_equal)

    def test_simple_init(self):
        """Test simple initialisation"""

        structure_file = "data/survey_structure_2021.xml"
        survey = LimeSurvey(
            structure_file=structure_file,
        )

        structure_dict = read_lime_questionnaire_structure(structure_file)
        section_df = pd.DataFrame(structure_dict["sections"])
        section_df = section_df.set_index("id")
        question_df = pd.DataFrame(structure_dict["questions"])
        question_df = question_df.set_index("name")

        self.assertEqual(
            survey.structure["sections"],
            section_df,
        )
        self.assertEqual(
            survey.structure["questions"],
            question_df,
        )

    def test_init_cmap(self):
        """Test initialisation with default cmap option for plotting"""

        structure_file = "data/survey_structure_2021.xml"
        cmap = "Blues"
        survey = LimeSurvey(
            structure_file=structure_file,
            cmap=cmap,
        )

        self.assertEqual(
            survey.cmap,
            cmap,
        )

    def test_init_output_folder(self):
        """Test initialisation with output folder option for plotting"""

        structure_file = "data/survey_structure_2021.xml"
        output_dir = ".."
        survey = LimeSurvey(
            structure_file=structure_file,
            output_folder=output_dir,
        )

        self.assertEqual(
            survey.output_folder,
            output_dir,
        )

    def test_init_figsize(self):
        """Test initialisation with default figsize option for plotting"""

        structure_file = "data/survey_structure_2021.xml"
        figsize = (10, 15)
        survey = LimeSurvey(structure_file=structure_file, figsize=figsize)

        self.assertEqual(survey.figsize, figsize)


if __name__ == "__main__":
    unittest.main()
