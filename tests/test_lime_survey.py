"""Test functions related to Survey class"""
import os
import unittest

import pandas as pd
from pandas._testing import assert_frame_equal

from n2survey.lime import LimeSurvey, read_lime_questionnaire_structure

structure_file = "data/survey_structure_2021.xml"
response_file = "data/dummy_data_2021_codeonly.csv"


class TestLimeSurveyInitialisation(unittest.TestCase):
    """Test LimeSurvey class initialisation"""

    default_plot_options = {
        "cmap": "Blues",
        "output_folder": os.path.abspath(os.curdir),
        "figsize": (6, 8),
    }

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

        survey = LimeSurvey(
            structure_file=structure_file,
        )

        structure_dict = read_lime_questionnaire_structure(structure_file)
        section_df = pd.DataFrame(structure_dict["sections"])
        section_df = section_df.set_index("id")
        question_df = pd.DataFrame(structure_dict["questions"])
        for i in range(question_df.shape[0]):
            if question_df.loc[i]["format"] is None:
                if "Y" in question_df.loc[i]["choices"].keys():
                    question_df.loc[i, ["format"]] = "multiple_choice"
                elif "SQ" in question_df.loc[i]["name"]:
                    question_df.loc[i, ["format"]] = "array"
                else:
                    question_df.loc[i, ["format"]] = "single_choice"
        question_df["name"] = question_df["name"].str.replace("T", "_other")
        question_df = question_df.set_index("name")

        self.assertEqual(
            survey.sections,
            section_df,
        )
        self.assertEqual(
            survey.questions,
            question_df,
        )
        self.assertEqual(survey.plot_options["cmap"], self.default_plot_options["cmap"])
        self.assertEqual(
            survey.plot_options["output_folder"],
            self.default_plot_options["output_folder"],
        )
        self.assertEqual(
            survey.plot_options["figsize"], self.default_plot_options["figsize"]
        )

    def test_init_cmap(self):
        """Test initialisation with default cmap option for plotting"""

        cmap = "Reds"
        survey = LimeSurvey(
            structure_file=structure_file,
            cmap=cmap,
        )

        self.assertEqual(
            survey.plot_options["cmap"],
            cmap,
        )
        self.assertEqual(
            survey.plot_options["output_folder"],
            self.default_plot_options["output_folder"],
        )
        self.assertEqual(
            survey.plot_options["figsize"], self.default_plot_options["figsize"]
        )

    def test_init_output_folder(self):
        """Test initialisation with output folder option for plotting"""

        output_dir = "plot/"
        survey = LimeSurvey(
            structure_file=structure_file,
            output_folder=output_dir,
        )

        self.assertEqual(
            survey.plot_options["output_folder"],
            output_dir,
        )
        self.assertEqual(survey.plot_options["cmap"], self.default_plot_options["cmap"])
        self.assertEqual(
            survey.plot_options["figsize"], self.default_plot_options["figsize"]
        )

    def test_init_figsize(self):
        """Test initialisation with default figsize option for plotting"""

        figsize = (10, 15)
        survey = LimeSurvey(structure_file=structure_file, figsize=figsize)

        self.assertEqual(survey.plot_options["figsize"], figsize)
        self.assertEqual(survey.plot_options["cmap"], self.default_plot_options["cmap"])
        self.assertEqual(
            survey.plot_options["output_folder"],
            self.default_plot_options["output_folder"],
        )


class TestLimeSurveyReadResponse(unittest.TestCase):
    """Test LimeSurvey reading response"""

    def test_read_response(self):
        """Test reading response from dummy data csv"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_response(responses_file=response_file)

        first_question = survey.response.columns.get_loc("A00")
        last_question = survey.response.columns.get_loc("M1")
        missing_columns = [
            column
            for column in survey.response.columns[first_question:last_question]
            if column not in survey.questions.index and "other" not in column
        ]

        self.assertEqual(bool(missing_columns), False)

    def test_single_choice_dtype(self):
        """Test data for single choice questions is unordered categorical dtype"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_response(responses_file=response_file)

        single_choice_questions = [
            question
            for question in survey.questions.index
            if survey.questions.loc[question]["format"] == "single_choice"
        ]

        self.assertEqual(
            (survey.response[single_choice_questions].dtypes == "category").all(),
            True,
        )
        self.assertEqual(
            bool(
                [
                    column
                    for column in single_choice_questions
                    if survey.response[column].cat.ordered
                ]
            ),
            False,
        )

    def test_array_dtype(self):
        """Test data for array questions is ordered categorical dtype"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_response(responses_file=response_file)

        array_questions = [
            question
            for question in survey.questions.index
            if survey.questions.loc[question]["format"] == "array"
        ]

        self.assertEqual(
            (survey.response[array_questions].dtypes == "category").all(),
            True,
        )
        self.assertEqual(
            bool(
                [
                    column
                    for column in array_questions
                    if not survey.response[column].cat.ordered
                ]
            ),
            False,
        )

    def test_multiple_choice_dtype(self):
        """Test data for multiple choice questions is bool dtype"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_response(responses_file=response_file)

        multiple_choice_questions = [
            question
            for question in survey.questions.index
            if survey.questions.loc[question]["format"] == "multiple_choice"
        ]

        self.assertEqual(
            (survey.response[multiple_choice_questions].dtypes == "bool").all(),
            True,
        )


if __name__ == "__main__":
    unittest.main()
