"""Test functions related to Survey class"""
import os
import re
import unittest

import pandas as pd
from pandas._testing import assert_frame_equal

from n2survey.lime import LimeSurvey, read_lime_questionnaire_structure

STRUCTURE_FILE = "data/survey_structure_2021.xml"
RESPONSES_FILE = "data/dummy_data_2021_codeonly.csv"


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

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        structure_dict = read_lime_questionnaire_structure(STRUCTURE_FILE)
        section_df = pd.DataFrame(structure_dict["sections"])
        section_df = section_df.set_index("id")
        question_df = pd.DataFrame(structure_dict["questions"])
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
            structure_file=STRUCTURE_FILE,
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
            structure_file=STRUCTURE_FILE,
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
        survey = LimeSurvey(structure_file=STRUCTURE_FILE, figsize=figsize)

        self.assertEqual(survey.plot_options["figsize"], figsize)
        self.assertEqual(survey.plot_options["cmap"], self.default_plot_options["cmap"])
        self.assertEqual(
            survey.plot_options["output_folder"],
            self.default_plot_options["output_folder"],
        )


class TestLimeSurveyReadResponses(unittest.TestCase):
    """Test LimeSurvey reading responses"""

    def test_read_responses(self):
        """Test reading responses from dummy data csv"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)
        survey.read_responses(responses_file=RESPONSES_FILE)

        not_in_structure = list(
            set(survey.responses.columns) - set(survey.questions.index)
        )

        self.assertEqual(bool(not_in_structure), False)

    def test_single_choice_dtype(self):
        """Test data for single choice questions is unordered categorical dtype"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)
        survey.read_responses(responses_file=RESPONSES_FILE)

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

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)
        survey.read_responses(responses_file=RESPONSES_FILE)

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

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)
        survey.read_responses(responses_file=RESPONSES_FILE)

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

    def test_lime_system_info_dtypes(self):
        """Test data in lime_system_info has correct dtypes"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)
        survey.read_responses(responses_file=RESPONSES_FILE)

        datetime_columns = []
        float_columns = []
        categorical_columns = []
        for column in survey.lime_system_info.columns:
            if re.search("[Tt]ime", column):
                float_columns.append(column)
            if "date" in column:
                datetime_columns.append(column)
            if "language" in column:
                categorical_columns.append(column)

        self.assertEqual(
            (
                survey.lime_system_info[datetime_columns].dtypes == "datetime64[ns]"
            ).all(),
            True,
        )
        self.assertEqual(
            (survey.lime_system_info[float_columns].dtypes == "float64").all(),
            True,
        )
        self.assertEqual(
            (survey.lime_system_info[categorical_columns].dtypes == "category").all(),
            True,
        )


class TestLimeSurveyGetLabels(unittest.TestCase):
    """Test LimeSurvey get_label"""

    def test_single_choice_label(self):
        """Test getting label for single-choice question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        single_choice_questions = survey.questions.loc[
            survey.questions["type"] == "single-choice", "question_group"
        ].unique()
        test_question = single_choice_questions[3]
        label = survey.get_label(test_question)

        self.assertDictEqual(
            label,
            {test_question: survey.questions.loc[test_question, "label"]},
        )

    def test_multiple_choice_label(self):
        """Test getting label for multiple-choice question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        multiple_choice_questions = survey.questions.loc[
            survey.questions["type"] == "multiple-choice", "question_group"
        ].unique()
        test_question = multiple_choice_questions[3]
        label = survey.get_label(test_question)

        self.assertDictEqual(
            label,
            {test_question: survey.questions.loc[test_question + "_SQ001", "label"]},
        )

    def test_array_label(self):
        """Test getting label for array question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        array_questions = survey.questions.loc[
            survey.questions["type"] == "array", "question_group"
        ].unique()
        test_question = array_questions[3]
        label = survey.get_label(test_question)

        question_group = survey.questions[
            survey.questions["question_group"] == test_question
        ]
        label_dict = {
            index: label
            for index, label in zip(question_group.index, question_group["label"])
        }
        label_dict["question_label"] = question_group.iloc[0]["question_label"]

        self.assertDictEqual(
            label,
            label_dict,
        )


class TestLimeSurveyGetChoices(unittest.TestCase):
    """Test LimeSurvey get_choices"""

    def test_single_choice_choices(self):
        """Test getting choices for single-choice question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        single_choice_questions = survey.questions.loc[
            survey.questions["type"] == "single-choice", "question_group"
        ].unique()
        test_question = single_choice_questions[3]
        choices = survey.get_choices(test_question)

        self.assertDictEqual(
            choices,
            {test_question: survey.questions.loc[test_question, "choices"]},
        )

    def test_array_choices(self):
        """Test getting choices for array question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        array_questions = survey.questions.loc[
            survey.questions["type"] == "array", "question_group"
        ].unique()
        test_question = array_questions[3]
        choices = survey.get_choices(test_question)

        self.assertDictEqual(
            choices,
            {test_question: survey.questions.loc[test_question + "_SQ001", "choices"]},
        )

    def test_multiple_choice_choices(self):
        """Test getting choices for multiple-choice question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        multiple_choice_questions = survey.questions.loc[
            survey.questions["type"] == "multiple-choice", "question_group"
        ].unique()
        test_question = multiple_choice_questions[3]
        choices = survey.get_choices(test_question)

        question_group = survey.questions[
            survey.questions["question_group"] == test_question
        ]
        choices_dict = {
            index: choices
            for index, choices in zip(question_group.index, question_group["choices"])
        }

        self.assertDictEqual(
            choices,
            choices_dict,
        )


if __name__ == "__main__":
    unittest.main()
