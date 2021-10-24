"""Test functions related to Survey class"""
import os
import re
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
        survey.read_responses(responses_file=response_file)

        not_in_structure = list(
            set(survey.responses.columns) - set(survey.questions.index)
        )

        self.assertEqual(bool(not_in_structure), False)

    def test_single_choice_dtype(self):
        """Test data for single choice questions is unordered categorical dtype"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_responses(responses_file=response_file)

        single_choice_columns = [
            column
            for column in survey.responses.columns
            if survey.questions.loc[column, "type"] == "single-choice"
            and survey.questions.loc[column, "format"] is None
        ]

        self.assertEqual(
            (survey.responses[single_choice_columns].dtypes == "category").all(),
            True,
        )

    def test_array_dtype(self):
        """Test data for array questions is ordered categorical dtype"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_responses(responses_file=response_file)

        array_columns = [
            column
            for column in survey.responses.columns
            if survey.questions.loc[column, "type"] == "array"
            and survey.questions.loc[column, "format"] is None
        ]

        self.assertEqual(
            (survey.responses[array_columns].dtypes == "category").all(),
            True,
        )

    def test_multiple_choice_dtype(self):
        """Test data for multiple choice questions is bool dtype"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_responses(responses_file=response_file)

        multiple_choice_columns = [
            column
            for column in survey.responses.columns
            if survey.questions.loc[column, "type"] == "multiple-choice"
            and survey.questions.loc[column, "format"] is None
        ]

        self.assertEqual(
            (survey.responses[multiple_choice_columns].dtypes == "category").all(),
            True,
        )

    def test_sys_info_dtypes(self):
        """Test data in sys_info has correct dtypes"""

        survey = LimeSurvey(structure_file=structure_file)
        survey.read_responses(responses_file=response_file)

        datetime_columns = []
        float_columns = []
        categorical_columns = []
        for column in survey.sys_info.columns:
            if re.search("[Tt]ime", column):
                float_columns.append(column)
            if "date" in column:
                datetime_columns.append(column)
            if "language" in column:
                categorical_columns.append(column)

        self.assertEqual(
            (survey.sys_info[datetime_columns].dtypes == "datetime64[ns]").all(),
            True,
        )
        self.assertEqual(
            (survey.sys_info[float_columns].dtypes == "float64").all(),
            True,
        )
        self.assertEqual(
            (survey.sys_info[categorical_columns].dtypes == "category").all(),
            True,
        )


if __name__ == "__main__":
    unittest.main()
