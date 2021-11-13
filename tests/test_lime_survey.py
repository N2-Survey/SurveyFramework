"""Test functions related to Survey class"""
import os
import re
import unittest

import pandas as pd
from pandas._testing import assert_frame_equal

from n2survey.lime import LimeSurvey, read_lime_questionnaire_structure

STRUCTURE_FILE = "data/survey_structure_2021.xml"
RESPONSES_FILE = "data/dummy_data_2021_codeonly.csv"

default_test_questions = {
    "single-choice": "A6",
    "multiple-choice": "C3",
    "array": "B6",
    "free": "A8",
}


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


class TestLimeSurveyGetLabel(unittest.TestCase):
    """Test LimeSurvey get_label"""

    def test_single_choice_label(self):
        """Test getting label for single-choice question with question id"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        label = survey.get_label(default_test_questions["single-choice"])

        self.assertEqual(
            label,
            "To which gender do you identify most?",
        )

    def test_multiple_choice_label_by_group(self):
        """Test getting label for multiple-choice question with question group id"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        label = survey.get_label(default_test_questions["multiple-choice"])

        self.assertEqual(
            label,
            "What was/were the reason(s) for considering to quit your PhD?",
        )

    def test_multiple_choice_label_by_subquestion(self):
        """Test getting label for multiple-choice question with subquestion id"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        label = survey.get_label(default_test_questions["multiple-choice"] + "_SQ001")

        self.assertEqual(
            label,
            "What was/were the reason(s) for considering to quit your PhD?",
        )

    def test_array_label_by_group(self):
        """Test getting label for array question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        label = survey.get_label(default_test_questions["array"])

        self.assertEqual(
            label,
            "Would it be possible for you to extend your current contract/stipend for the following reasons?",
        )

    def test_array_label_by_subquestion(self):
        """Test getting label for array question with subquestion id"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        label = survey.get_label(default_test_questions["array"] + "_SQ001")

        self.assertEqual(
            label,
            "More time needed to complete PhD project",
        )

    def test_free_label(self):
        """Test getting label for free input question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        label = survey.get_label(default_test_questions["free"])

        self.assertEqual(
            label,
            "When did you start your PhD?",
        )


class TestLimeSurveyGetChoices(unittest.TestCase):
    """Test LimeSurvey get_choices"""

    def test_single_choice_choices(self):
        """Test getting choices for single-choice question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        choices = survey.get_choices(default_test_questions["single-choice"])

        self.assertDictEqual(
            choices,
            {
                "A1": "Woman",
                "A3": "Man",
                "A4": "Gender diverse (Gender-fluid)",
                "A5": "Non-binary",
                "A2": "I don't want to answer this question",
                "-oth-": "Other gender representations:",
            },
        )

    def test_multiple_choice_choices_by_group(self):
        """Test getting choices for multiple-choice question with question group id"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        choices = survey.get_choices(default_test_questions["multiple-choice"])

        self.assertDictEqual(
            choices,
            {
                "C3_SQ001": "I do not like scientific work.",
                "C3_SQ002": "I do not like my topic.",
                "C3_SQ003": "I have problems getting by financially.",
                "C3_SQ004": "I do not like my working conditions.",
                "C3_SQ005": "I have work related difficulties with my supervisor.",
                "C3_SQ006": "I don’t like the social environment at my workplace.",
                "C3_SQ007": "I have personal difficulties with my supervisor.",
                "C3_SQ008": "I find my career prospective unattractive.",
                "C3_SQ009": "I have personal reasons.",
                "C3_SQ010": "I do not feel qualified enough.",
                "C3_SQ011": "I have no or poor academic results.",
                "C3_SQ012": "I find other jobs more interesting.",
                "C3_SQ013": "I can’t cope with the high workload.",
                "C3_SQ014": "My academic life is not compatible with my family responsibilities.",
                "C3_SQ015": "My project is not funded anymore.",
                "C3_SQ016": "I have administrative problems.",
                "C3_SQ020": "My health.",
                "C3_SQ017": "I don't want to answer this question.",
                "C3_SQ018": "I don't know.",
                "C3T": "Other, please specify",
            },
        )

    def test_multiple_choice_choices_by_subquestion(self):
        """Test getting choices for multiple-choice question with subquestion id"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        choices = survey.get_choices(
            default_test_questions["multiple-choice"] + "_SQ001"
        )

        self.assertDictEqual(
            choices,
            {"Y": "I do not like scientific work."},
        )

    def test_array_choices_by_group(self):
        """Test getting choices for array question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        choices = survey.get_choices(default_test_questions["array"])

        self.assertDictEqual(
            choices,
            {
                "B6_SQ001": "More time needed to complete PhD project",
                "B6_SQ002": "Parental leave",
                "B6_SQ003": "Wrap-up phase after completion of the PhD project",
            },
        )

    def test_array_choices_by_subquestion(self):
        """Test getting choices for array question with subquestion id"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        choices = survey.get_choices(default_test_questions["array"] + "_SQ001")

        self.assertDictEqual(
            choices,
            {
                "A1": "Yes",
                "A2": "No",
                "A3": "I don't know",
                "A4": "I don't want to answer this question",
            },
        )

    def test_free_choices(self):
        """Test getting choices for free input question"""

        survey = LimeSurvey(structure_file=STRUCTURE_FILE)

        label = survey.get_choices(default_test_questions["free"])

        self.assertEqual(
            label,
            None,
        )


if __name__ == "__main__":
    unittest.main()
