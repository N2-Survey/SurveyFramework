"""Test functions related to Survey class"""
import os
import re
import unittest

import numpy as np
import pandas as pd

from n2survey.lime import DEFAULT_THEME, LimeSurvey, read_lime_questionnaire_structure
from tests.common import (
    BaseTestLimeSurvey2021Case,
    BaseTestLimeSurvey2021WithResponsesCase,
)


class TestLimeSurveyInitialisation(BaseTestLimeSurvey2021Case):
    """Test LimeSurvey class initialisation"""

    def test_simple_init(self):
        """Test simple initialisation"""

        survey = LimeSurvey(structure_file=self.structure_file)

        structure_dict = read_lime_questionnaire_structure(self.structure_file)
        section_df = pd.DataFrame(structure_dict["sections"])
        section_df = section_df.set_index("id")
        question_df = pd.DataFrame(structure_dict["questions"])
        question_df = question_df.set_index("name")
        question_df["is_contingent"] = question_df.contingent_of_name.notnull()
        transformation_questions = {
            "state_anxiety_score": {
                "label": "What is the state anxiety score?",
                "type": "free",
                "is_contingent": False,
            },
            "state_anxiety_class": {
                "label": "What is the state anxiety class?",
                "type": "single-choice",
                "choices": {
                    "A1": "no or low anxiety",
                    "A2": "moderate anxiety",
                    "A3": "high anxiety",
                },
                "is_contingent": False,
            },
            "trait_anxiety_score": {
                "label": "What is the trait anxiety score?",
                "type": "free",
                "is_contingent": False,
            },
            "trait_anxiety_class": {
                "label": "What is the trait anxiety class?",
                "type": "single-choice",
                "choices": {
                    "A1": "no or low anxiety",
                    "A2": "moderate anxiety",
                    "A3": "high anxiety",
                },
                "is_contingent": False,
            },
            "depression_score": {
                "label": "What is the depression score?",
                "type": "free",
                "is_contingent": False,
            },
            "depression_class": {
                "label": "What is the depression class?",
                "type": "single-choice",
                "choices": {
                    "A1": "no to minimal depression",
                    "A2": "mild depression",
                    "A3": "moderate depression",
                    "A4": "moderately severe depression",
                    "A5": "severe depression",
                },
                "is_contingent": False,
            },
            "noincome_duration": {
                "label": "For how long have you been working on your PhD without pay?",
                "type": "free",
                "is_contingent": False,
            },
            "income_amount": {
                "label": "Right now, what is your monthly net income for your work at your research organization?",
                "type": "free",
                "is_contingent": False,
            },
            "costs_amount": {
                "label": "How much do you pay for your rent and associated living costs per month in euros?",
                "type": "free",
                "is_contingent": False,
            },
            "contract_duration": {
                "label": "What was or is the longest duration of your contract or stipend related to your PhD project?",
                "type": "free",
                "is_contingent": False,
            },
            "holiday_amount": {
                "label": "How many holidays per year can you take according to your contract or stipend?",
                "type": "free",
                "is_contingent": False,
            },
            "hours_amount": {
                "label": "On average, how many hours do you typically work per week in total?",
                "type": "free",
                "is_contingent": False,
            },
            "holidaytaken_amount": {
                "label": "How many days did you take off (holiday) in the past year?",
                "type": "free",
                "is_contingent": False,
            },
            "formal_supervision_score": {
                "label": "What is the formal supervision score?",
                "type": "free",
                "is_contingent": False,
            },
            "formal_supervision_class": {
                "label": "What is the formal supervision class?",
                "type": "single-choice",
                "choices": {
                    "A1": "very satisfied",
                    "A2": "rather satisfied",
                    "A3": "neither satisfied nor dissatisfied",
                    "A4": "rather dissatisfied",
                    "A5": "very dissatisfied",
                },
                "is_contingent": False,
            },
            "direct_supervision_score": {
                "label": "What is the direct supervision score?",
                "type": "free",
                "is_contingent": False,
            },
            "direct_supervision_class": {
                "label": "What is the direct supervision class?",
                "type": "single-choice",
                "choices": {
                    "A1": "very satisfied",
                    "A2": "rather satisfied",
                    "A3": "neither satisfied nor dissatisfied",
                    "A4": "rather dissatisfied",
                    "A5": "very dissatisfied",
                },
                "is_contingent": False,
            },
        }
        question_df = pd.concat(
            [
                question_df,
                pd.DataFrame(
                    data=transformation_questions.values(),
                    index=transformation_questions.keys(),
                ),
            ]
        )

        self.assertEqual(survey.sections, section_df)
        self.assertEqual(survey.questions, question_df)
        self.assertEqual(survey.theme, DEFAULT_THEME)
        self.assertEqual(survey.output_folder, os.path.abspath(os.curdir))

    def test_init_params(self):
        """Test initialisation with default cmap option for plotting"""

        survey = LimeSurvey(
            theme={"palette": "Reds"},
            output_folder="somefolder",
            structure_file=self.structure_file,
        )
        expected_theme = DEFAULT_THEME.copy()
        expected_theme["palette"] = "Reds"
        self.assertEqual(survey.theme, expected_theme)
        self.assertEqual(survey.output_folder, "somefolder")


class TestLimeSurveyReadResponses(BaseTestLimeSurvey2021WithResponsesCase):
    """Test LimeSurvey reading responses"""

    def test_read_responses(self):
        """Test reading responses from dummy data csv"""

        not_in_structure = list(
            set(self.survey.responses.columns) - set(self.survey.questions.index)
        )

        self.assertEqual(bool(not_in_structure), False)

    def test_mental_health_transformation_questions(self):
        """Test adding responses to mental health transformationquestions in
        read_responses"""

        mental_health_questions = {
            "state_anxiety": "D1",
            "trait_anxiety": "D2",
            "depression": "D3",
        }

        survey = LimeSurvey(structure_file=self.structure_file)
        survey.read_responses(
            responses_file=self.responses_file,
            transformation_questions=mental_health_questions,
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

        self.assert_df_equal(
            survey.responses.iloc[:3, -6:], ref, msg="DataFrames not equal."
        )

    def test_supervision_transformation_questions(self):
        """Test adding responses to supervision transformation questions in
        read_responses"""

        supervision_questions = {"supervision": ["E7a", "E7b"]}

        survey = LimeSurvey(structure_file=self.structure_file)
        survey.read_responses(
            responses_file=self.responses_file,
            transformation_questions=supervision_questions,
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
        self.assert_df_equal(
            survey.responses.iloc[6:9, -4:], ref, msg="DataFrames not equal."
        )

    def test_range_to_numerical_transformation_questions(self):
        """Test adding responses to range_to_numerical transformation questions
        in read_responses"""

        range_questions = {"range": ["B1b", "B2", "B3", "B4", "B10", "C4", "C8"]}

        survey = LimeSurvey(structure_file=self.structure_file)
        survey.read_responses(
            responses_file=self.responses_file,
            transformation_questions=range_questions,
        )
        ref = pd.DataFrame(
            data={
                "noincome_duration": [np.NaN, np.NaN, np.NaN],
                "income_amount": [1650.0, 1950.0, 2050.0],
                "costs_amount": [850.0, 750.0, 550.0],
                "contract_duration": [30.0, 48.0, 30.0],
                "holiday_amount": [28.0, 28.0, 28.0],
                "hours_amount": [53.0, 38.0, 43.0],
                "holidaytaken_amount": [8.0, 28.0, 13.0],
            },
            index=[2, 3, 4],
        )
        ref.index.name = "id"
        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(
            survey.responses.iloc[:3, -7:], ref, msg="DataFrames not equal."
        )

    def test_single_choice_dtype(self):
        """Test data for single choice questions is unordered categorical dtype"""

        single_choice_columns = [
            column
            for column in self.survey.responses.columns
            if self.survey.questions.loc[column, "type"] == "single-choice"
            and self.survey.questions.loc[column, "format"] is None
        ]

        self.assertEqual(
            (self.survey.responses[single_choice_columns].dtypes == "category").all(),
            True,
        )

    def test_array_dtype(self):
        """Test data for array questions is ordered categorical dtype"""

        array_columns = [
            column
            for column in self.survey.responses.columns
            if self.survey.questions.loc[column, "type"] == "array"
            and self.survey.questions.loc[column, "format"] is None
        ]

        self.assertEqual(
            (self.survey.responses[array_columns].dtypes == "category").all(),
            True,
        )

    def test_multiple_choice_dtype(self):
        """Test data for multiple choice questions is bool dtype"""

        multiple_choice_columns = [
            column
            for column in self.survey.responses.columns
            if self.survey.questions.loc[column, "type"] == "multiple-choice"
            and self.survey.questions.loc[column, "format"] is None
        ]

        self.assertEqual(
            (self.survey.responses[multiple_choice_columns].dtypes == "category").all(),
            True,
        )

    def test_lime_system_info_dtypes(self):
        """Test data in lime_system_info has correct dtypes"""

        datetime_columns = []
        float_columns = []
        categorical_columns = []
        for column in self.survey.lime_system_info.columns:
            if re.search("[Tt]ime", column):
                float_columns.append(column)
            if "date" in column:
                datetime_columns.append(column)
            if "language" in column:
                categorical_columns.append(column)

        self.assertEqual(
            (
                self.survey.lime_system_info[datetime_columns].dtypes
                == "datetime64[ns]"
            ).all(),
            True,
        )
        self.assertEqual(
            (self.survey.lime_system_info[float_columns].dtypes == "float64").all(),
            True,
        )
        self.assertEqual(
            (
                self.survey.lime_system_info[categorical_columns].dtypes == "category"
            ).all(),
            True,
        )


class TestLimeSurveyTransformQuestion(BaseTestLimeSurvey2021WithResponsesCase):
    """Test LimeSurvey transform_question"""

    def test_mental_health_transforms(self):
        """Test transforming three types of mental health questions"""

        state_anxiety_transformed = self.survey.transform_question(
            "D1", "state_anxiety"
        )
        trait_anxiety_transformed = self.survey.transform_question(
            "D2", "trait_anxiety"
        )
        depression_transformed = self.survey.transform_question("D3", "depression")

        state_anxiety_ref = pd.DataFrame(
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
        state_anxiety_ref.index.name = "id"

        trait_anxiety_ref = pd.DataFrame(
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
        trait_anxiety_ref.index.name = "id"

        depression_ref = pd.DataFrame(
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
        depression_ref.index.name = "id"

        self.assert_df_equal(
            state_anxiety_transformed.iloc[:3],
            state_anxiety_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            trait_anxiety_transformed.iloc[:3],
            trait_anxiety_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            depression_transformed.iloc[:3], depression_ref, msg="Series not equal"
        )

    def test_supervision_transforms(self):
        """Test transforming two types of supervision questions"""

        formal_supervision_transformed = self.survey.transform_question(
            "E7a", "supervision"
        )
        direct_supervision_transformed = self.survey.transform_question(
            "E7b", "supervision"
        )

        formal_supervision_ref = pd.DataFrame(
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
        formal_supervision_ref.index.name = "id"

        direct_supervision_ref = pd.DataFrame(
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
        direct_supervision_ref.index.name = "id"

        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(
            formal_supervision_transformed.iloc[6:9],
            formal_supervision_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            direct_supervision_transformed.iloc[6:9],
            direct_supervision_ref,
            msg="Series not equal",
        )

    def test_range_transforms(self):
        """Test transforming range to numerical questions"""

        single_choice_1_transformed = self.survey.transform_question("B1b", "range")
        single_choice_2_transformed = self.survey.transform_question("B2", "range")
        single_choice_3_transformed = self.survey.transform_question("B3", "range")
        single_choice_4_transformed = self.survey.transform_question("B4", "range")
        single_choice_5_transformed = self.survey.transform_question("B10", "range")
        single_choice_6_transformed = self.survey.transform_question("C4", "range")
        single_choice_7_transformed = self.survey.transform_question("C8", "range")

        single_choice_1_ref = pd.DataFrame(
            data={
                "noincome_duration": [np.NaN, np.NaN, np.NaN],
            },
            index=[2, 3, 4],
        )
        single_choice_1_ref.index.name = "id"

        single_choice_2_ref = pd.DataFrame(
            data={
                "income_amount": [1650.0, 1950.0, 2050.0],
            },
            index=[2, 3, 4],
        )
        single_choice_2_ref.index.name = "id"

        single_choice_3_ref = pd.DataFrame(
            data={
                "costs_amount": [850.0, 750.0, 550.0],
            },
            index=[2, 3, 4],
        )
        single_choice_3_ref.index.name = "id"

        single_choice_4_ref = pd.DataFrame(
            data={
                "contract_duration": [30.0, 48.0, 30.0],
            },
            index=[2, 3, 4],
        )
        single_choice_4_ref.index.name = "id"

        single_choice_5_ref = pd.DataFrame(
            data={
                "holiday_amount": [28.0, 28.0, 28.0],
            },
            index=[2, 3, 4],
        )
        single_choice_5_ref.index.name = "id"

        single_choice_6_ref = pd.DataFrame(
            data={
                "hours_amount": [53.0, 38.0, 43.0],
            },
            index=[2, 3, 4],
        )
        single_choice_6_ref.index.name = "id"

        single_choice_7_ref = pd.DataFrame(
            data={
                "holidaytaken_amount": [8.0, 28.0, 13.0],
            },
            index=[2, 3, 4],
        )
        single_choice_7_ref.index.name = "id"

        # "id" of dataframe starts at 2, therefore difference to "index" above
        self.assert_df_equal(
            single_choice_1_transformed.iloc[:3],
            single_choice_1_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            single_choice_2_transformed.iloc[:3],
            single_choice_2_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            single_choice_3_transformed.iloc[:3],
            single_choice_3_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            single_choice_4_transformed.iloc[:3],
            single_choice_4_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            single_choice_5_transformed.iloc[:3],
            single_choice_5_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            single_choice_6_transformed.iloc[:3],
            single_choice_6_ref,
            msg="Series not equal",
        )
        self.assert_df_equal(
            single_choice_7_transformed.iloc[:3],
            single_choice_7_ref,
            msg="Series not equal",
        )


class TestLimeSurveyAddQuestion(BaseTestLimeSurvey2021Case):
    """Test LimeSurvey add_question"""

    def test_add_question_without_responses(self):
        """Test adding question without responses"""

        survey = LimeSurvey(structure_file=self.structure_file)
        survey.read_responses(responses_file=self.responses_file)
        survey.add_question(
            name="X69",
            type="single-choice",
            label="Not a great question",
            choices={"A1": "Yes", "A2": "Also yes", "A3": "Why not"},
        )

        ref = pd.Series(
            {
                "label": "Not a great question",
                "format": np.nan,
                "choices": {"A1": "Yes", "A2": "Also yes", "A3": "Why not"},
                "question_group": np.nan,
                "question_label": np.nan,
                "question_description": np.nan,
                "type": "single-choice",
                "section_id": np.nan,
                "contingent_of_name": np.nan,
                "contingent_of_choice": np.nan,
                "is_contingent": False,
            },
            name="X69",
        )

        self.assert_series_equal(
            ref, survey.questions.loc["X69"], msg="Series not equal"
        )

    def test_add_question_with_responses(self):
        """Test adding question with responses"""

        survey = LimeSurvey(structure_file=self.structure_file)
        survey.read_responses(responses_file=self.responses_file)
        my_responses = pd.Series({2: "1", 3: "2", 4: "3"})
        survey.add_question(
            name="X69",
            type="free",
            label="Another not great question",
            responses=my_responses,
        )

        self.assert_series_equal(
            pd.Series({2: "1", 3: "2", 4: "3", 5: np.nan, 6: np.nan}, name="X69"),
            survey.responses.loc[[2, 3, 4, 5, 6], "X69"],
            msg="Series not equal",
        )


class TestLimeSurveyAddResponses(BaseTestLimeSurvey2021Case):
    """Test LimeSurvey add_responses"""

    def test_add_responses_without_question(self):
        """Test adding responses without question name"""

        survey = LimeSurvey(structure_file=self.structure_file)
        survey.read_responses(responses_file=self.responses_file)
        my_responses = pd.Series({2: "1", 3: "2", 4: "3"}, name="X69")
        survey.add_responses(my_responses)

        self.assert_series_equal(
            pd.Series({2: "1", 3: "2", 4: "3", 5: np.nan, 6: np.nan}, name="X69"),
            survey.responses.loc[[2, 3, 4, 5, 6], "X69"],
            msg="Series not equal",
        )

    def test_add_responses_with_question(self):
        """Test adding responses with question name"""

        survey = LimeSurvey(structure_file=self.structure_file)
        survey.read_responses(responses_file=self.responses_file)
        my_responses = pd.Series({2: "1", 3: "2", 4: "3"}, name="X69")
        survey.add_responses(my_responses, question="A42")

        self.assert_series_equal(
            pd.Series({2: "1", 3: "2", 4: "3", 5: np.nan, 6: np.nan}, name="A42"),
            survey.responses.loc[[2, 3, 4, 5, 6], "A42"],
            msg="Series not equal",
        )


class TestLimeSurveyGetResponse(BaseTestLimeSurvey2021WithResponsesCase):
    """Test LimeSurvey get response"""

    def test_get_response(self):
        """Test basic get response functionality for valid and invalid input"""
        questions = ["A1", "A3", "A4", "A5", "A10", "A14", "B6", "D2", "E5a", "E9"]
        for question in questions:
            self.survey.get_responses(question, labels=False)
            self.survey.get_responses(question, labels=True)

        # assume exception raised after invalid question name
        self.assertRaises(ValueError, self.survey.get_responses, "X2", labels=False)
        self.assertRaises(ValueError, self.survey.get_responses, "X2", labels=True)

        # assume exception is thrown after A2 missing in responses
        self.assertRaises(KeyError, self.survey.get_responses, "A2", labels=False)
        self.assertRaises(KeyError, self.survey.get_responses, "A2", labels=True)

    def test_get_response_single_choice(self):
        """Test get response for single choice question type"""
        expected_response = [
            ["A1", "nan"],
            ["A1", "nan"],
            ["A3", "nan"],
            ["A2", "nan"],
            ["nan", "nan"],
        ]
        response = self.survey.get_responses(self.single_choice_column, labels=False)
        np.testing.assert_array_equal(
            expected_response, response.values.astype(str)[:5]
        )

        expected_response = [
            ["Woman", "nan"],
            ["Woman", "nan"],
            ["Man", "nan"],
            ["I don't want to answer this question", "nan"],
            ["No Answer", "nan"],
        ]
        response = self.survey.get_responses(self.single_choice_column, labels=True)
        expected_columns = [
            "To which gender do you identify most?",
            "To which gender do you identify most? / Other gender representations:",
        ]
        np.testing.assert_array_equal(expected_columns, response.columns)
        np.testing.assert_array_equal(
            expected_response, response.values.astype(str)[:5]
        )

    def test_get_response_multiple_choice(self):
        """Test get response for multiple choice question type"""
        expected_response = [
            [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                np.nan,
            ],
            [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                np.nan,
            ],
        ]
        response = self.survey.get_responses(self.multiple_choice_column, labels=False)
        np.testing.assert_equal(
            expected_response, response.values[:2].astype(np.float64)
        )

        expected_columns = [
            "I do not like scientific work.",
            "I do not like my topic.",
            "I have problems getting by financially.",
            "I do not like my working conditions.",
        ]
        response = self.survey.get_responses(self.multiple_choice_column, labels=True)
        np.testing.assert_array_equal(expected_columns, response.columns[:4])
        np.testing.assert_array_equal(
            expected_response, response.values[:2].astype(np.float64)
        )

    def test_get_response_multiple_choice_subquestion(self):
        """Test get response for subquestion of multiple choice question type"""
        expected_response = np.asarray(
            [
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                True,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
                False,
            ],
        ).reshape(36, 1)
        response = self.survey.get_responses(
            self.multiple_choice_column + "_SQ001", labels=False
        )
        np.testing.assert_equal(expected_response, response.values)

        expected_columns = ["I do not like scientific work."]
        response = self.survey.get_responses(
            self.multiple_choice_column + "_SQ001", labels=True
        )
        np.testing.assert_array_equal(expected_columns, response.columns)
        np.testing.assert_array_equal(expected_response, response.values)

    def test_get_response_free(self):
        """Test get response for free question type"""
        expected_response = pd.to_datetime(
            [
                "2017-01-01 00:00:00",
                "2020-06-01 00:00:00",
                "2019-08-01 00:00:00",
                "2017-05-01 00:00:00",
                "",
                "2017-08-01 00:00:00",
                "2018-01-01 00:00:00",
                "2020-09-01 00:00:00",
                "2017-08-01 00:00:00",
                "2019-12-01 00:00:00",
            ]
        )
        response = self.survey.get_responses(self.free_column, labels=False)
        self.assertEqual(response.shape[1], 1)
        np.testing.assert_array_equal(
            expected_response.values, response.iloc[:10, 0].values
        )

        expected_columns = ["When did you start your PhD?"]
        response = self.survey.get_responses(self.free_column, labels=True)
        np.testing.assert_array_equal(expected_columns, response.columns)
        np.testing.assert_array_equal(
            expected_response.values, response.iloc[:10, 0].values
        )

    def test_get_response_array(self):
        """Test get response for array question type"""
        expected_response = [
            ["A1", "A1", "A2"],
            ["A1", "A1", "A1"],
            ["A1", "A1", "A3"],
            ["A1", "A1", "A1"],
            ["nan", "nan", "nan"],
        ]
        response = self.survey.get_responses(self.array_column, labels=False)
        np.testing.assert_array_equal(
            expected_response, response.values[:5].astype(str)
        )

        expected_response = [
            ["Yes", "Yes", "No"],
            ["Yes", "Yes", "Yes"],
            ["Yes", "Yes", "I don't know"],
            ["Yes", "Yes", "Yes"],
            ["No Answer", "No Answer", "No Answer"],
        ]
        expected_columns = [
            "More time needed to complete PhD project",
            "Parental leave",
            "Wrap-up phase after completion of the PhD project",
        ]
        response = self.survey.get_responses(self.array_column, labels=True)
        np.testing.assert_array_equal(expected_columns, response.columns)
        np.testing.assert_array_equal(
            expected_response, response.values[:5].astype(str)
        )


# TODO:
# class TestLimeSurveyCount(BaseTestLimeSurvey2021WithResponsesCase):
#     """Test `count` method"""
#
#     def test_single_choice(self):
#         pass
#
#     def test_free(self):
#         pass
#
#     def test_array(self):
#         pass
#
#     def test_multiple_choice(self):
#         pass
#
#     def test_single_column(self):
#         pass


class TestLimeSurveyGetQuestionType(BaseTestLimeSurvey2021Case):
    """Test LimeSurvey get_question_type method"""

    def test_basic_question_types(self):
        self.assertEqual(
            "single-choice", self.survey.get_question_type(self.single_choice_column)
        )
        self.assertEqual(
            "multiple-choice",
            self.survey.get_question_type(self.multiple_choice_column),
        )
        self.assertEqual("array", self.survey.get_question_type(self.array_column))
        self.assertEqual("free", self.survey.get_question_type(self.free_column))

    def test_unexpected_type(self):
        self.survey.questions.loc[self.free_column, "type"] = "newtype"
        self.assertRaises(
            AssertionError, self.survey.get_question_type, self.free_column
        )

    def test_inconsistent_types(self):
        columns = self.survey.questions.index[
            self.survey.questions.question_group == self.array_column
        ]
        columns = list(columns)
        self.survey.questions.loc[columns[0], "type"] = "newtype"
        self.assertRaises(
            AssertionError, self.survey.get_question_type, self.array_column
        )


class TestLimeSurveyGetLabel(BaseTestLimeSurvey2021Case):
    """Test LimeSurvey get_label"""

    def test_single_choice_label(self):
        """Test getting label for single-choice question with question id"""

        label = self.survey.get_label(self.single_choice_column)

        self.assertEqual(
            label,
            "To which gender do you identify most?",
        )

    def test_multiple_choice_label_by_group(self):
        """Test getting label for multiple-choice question with question group id"""

        label = self.survey.get_label(self.multiple_choice_column)

        self.assertEqual(
            label,
            "What was/were the reason(s) for considering to quit your PhD?",
        )

    def test_multiple_choice_label_by_subquestion(self):
        """Test getting label for multiple-choice question with subquestion id"""

        label = self.survey.get_label(self.multiple_choice_column + "_SQ001")

        self.assertEqual(
            label,
            "What was/were the reason(s) for considering to quit your PhD?",
        )

    def test_array_label_by_group(self):
        """Test getting label for array question"""

        label = self.survey.get_label(self.array_column)

        self.assertEqual(
            label,
            "Would it be possible for you to extend your current contract/stipend for the following reasons?",
        )

    def test_array_label_by_subquestion(self):
        """Test getting label for array question with subquestion id"""

        label = self.survey.get_label(self.array_column + "_SQ001")

        self.assertEqual(
            label,
            "More time needed to complete PhD project",
        )

    def test_free_label(self):
        """Test getting label for free input question"""

        label = self.survey.get_label(self.free_column)

        self.assertEqual(
            label,
            "When did you start your PhD?",
        )


class TestLimeSurveyGetChoices(BaseTestLimeSurvey2021Case):
    """Test LimeSurvey get_choices"""

    def test_single_choice_choices(self):
        """Test getting choices for single-choice question"""

        choices = self.survey.get_choices(self.single_choice_column)

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

        choices = self.survey.get_choices(self.multiple_choice_column)

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

        choices = self.survey.get_choices(self.multiple_choice_column + "_SQ001")

        self.assertDictEqual(
            choices,
            {"Y": "I do not like scientific work."},
        )

    def test_array_choices(self):
        """Test getting choices for array question and sub-question"""

        question_choices = self.survey.get_choices(self.array_column)
        subquestion_choices = self.survey.get_choices(self.array_column + "_SQ001")

        self.assertDictEqual(
            question_choices,
            {
                "A1": "Yes",
                "A2": "No",
                "A3": "I don't know",
                "A4": "I don't want to answer this question",
            },
        )
        self.assertDictEqual(question_choices, subquestion_choices)

    def test_free_choices(self):
        """Test getting choices for free input question"""

        label = self.survey.get_choices(self.free_column)

        self.assertEqual(
            label,
            None,
        )


class TestLimeSurveyplot(BaseTestLimeSurvey2021WithResponsesCase):
    def test_single_choice_question(self):
        # Todo implement test using mocking or matplotlib.testing
        # mock_plot = create_autospec(LimeSurvey.plot)
        # plot_call_multi = mock_plot()

        self.survey.plot(
            self.multiple_choice_column,
            rc={"font.sans-serif": "Tahoma"},
            display_title=True,
        )

        self.survey.plot(
            self.single_choice_column,
            rc={"font.sans-serif": "Tahoma"},
            palette="colorblind",
        )


class TestLimeSurveyGetItem(BaseTestLimeSurvey2021WithResponsesCase):
    """Test LimeSurvey __getitem__ method"""

    def test_str(self):
        """Test __getitem__ for str input"""

        filtered_survey = self.survey[self.single_choice_column]

        ref = [
            "A1",
            "A1",
            "A3",
            "A2",
            np.nan,
            "A1",
            "A1",
            "A1",
            "A1",
            "A1",
            np.nan,
            "A1",
            "A1",
            "A1",
            "A1",
            np.nan,
            "A1",
            "A1",
            "A1",
            "A4",
            "A3",
            "A5",
            "A5",
            "A1",
            "A3",
            "A1",
            "A1",
            "A3",
            "A1",
            "A3",
            "A3",
            np.nan,
            "A3",
            "A5",
            "A3",
            "A3",
        ]

        np.testing.assert_equal(list(filtered_survey.responses.values[:, 0]), ref)

    def test_list(self):
        """Test __getitem__ for list of str input"""

        filtered_survey = self.survey[[self.array_column, self.single_choice_column]]

        ref = [
            "A2",
            "A1",
            "A3",
            "A1",
            np.nan,
            "A2",
            "A1",
            "A1",
            "A2",
            "A2",
            np.nan,
            "A1",
            "A2",
            "A3",
            "A2",
            np.nan,
            "A3",
            "A2",
            "A1",
            np.nan,
            "A3",
            "A2",
            np.nan,
            "A4",
            "A3",
            "A3",
            "A3",
            "A1",
            "A2",
            "A3",
            "A1",
            np.nan,
            "A3",
            "A3",
            "A3",
            "A3",
        ]

        np.testing.assert_equal(list(filtered_survey.responses.values[:, 2]), ref)

    def test_single_choice(self):
        """Test __getitem__ for single-choice question"""

        filtered_survey = self.survey[self.survey.responses.loc[:, "A3"] == "A3"]

        np.testing.assert_equal(np.array(filtered_survey.responses.index), [4, 37])
        np.testing.assert_equal(filtered_survey.responses.values[:, 7], ["A11", "A7"])

    def test_multiple_choice(self):
        """Test __getitem__ for multiple-choice question"""

        filtered_survey = self.survey[self.survey.responses.loc[:, "A10_SQ005"] == "Y"]

        np.testing.assert_equal(np.array(filtered_survey.responses.index), [31, 45])
        np.testing.assert_equal(filtered_survey.responses.values[:, 7], ["A10", "A7"])

    def test_array(self):
        """Test __getitem__ for array question"""

        filtered_survey = self.survey[self.survey.responses.loc[:, "C1_SQ005"] == "A5"]

        np.testing.assert_equal(np.array(filtered_survey.responses.index), [10, 39, 45])
        np.testing.assert_equal(
            filtered_survey.responses.values[:, 7], ["A8", "A9", "A7"]
        )

    def test_list_choices(self):
        """Test __getitem__ for list of choices to one question"""

        filtered_survey = self.survey[
            (self.survey.responses.loc[:, "B2"] == "A2")
            | (self.survey.responses.loc[:, "B2"] == "A5")
        ]

        np.testing.assert_equal(np.array(filtered_survey.responses.index), [28, 38, 39])
        np.testing.assert_equal(
            filtered_survey.responses.values[:, 7], ["A25", "A32", "A9"]
        )

    def test_list_questions(self):
        """Test __getitem__ for list of choices to one question"""

        filtered_survey = self.survey[
            (self.survey.responses.loc[:, "A11"] == "A1")
            & (
                (self.survey.responses.loc[:, "B9b_SQ001"] == "Y")
                | (self.survey.responses.loc[:, "B9b_SQ002"] == "Y")
            )
        ]

        np.testing.assert_equal(np.array(filtered_survey.responses.index), [5, 21, 46])
        np.testing.assert_equal(
            filtered_survey.responses.values[:, 7], ["A38", "A11", "A8"]
        )

    def test_tuple(self):
        """Test __getitem__ for tuple input"""

        filtered_survey = self.survey[
            self.survey.responses[self.single_choice_column] == "A5", "A5"
        ]

        ref = ["A25", "A4", "A7"]

        np.testing.assert_equal(filtered_survey.responses.values[:, 0], ref)

    def test_tuple_list(self):
        """Test __getitem__ for tuple input with list as second element"""

        filtered_survey = self.survey[
            self.survey.responses[self.single_choice_column] == "A5",
            [self.array_column, self.multiple_choice_column],
        ]

        ref = [np.nan, np.nan, "Y"]

        np.testing.assert_equal(list(filtered_survey.responses.values[:, 6]), ref)


class TestLimeSurveyQuery(BaseTestLimeSurvey2021WithResponsesCase):
    """Test LimeSurvey query method"""

    def test_single_choice(self):
        """Test query for single-choice question"""

        filtered_survey = self.survey.query("A3 == 'A3'")

        np.testing.assert_equal(list(filtered_survey.responses.index), [4, 37])

    def test_multiple_choice(self):
        """Test query for multiple-choice question"""

        filtered_survey = self.survey.query("A10_SQ005 == 'Y'")

        np.testing.assert_equal(list(filtered_survey.responses.index), [31, 45])

    def test_array(self):
        """Test query for array question"""

        filtered_survey = self.survey.query("C1_SQ005 == 'A5'")

        np.testing.assert_equal(list(filtered_survey.responses.index), [10, 39, 45])

    def test_list_choices(self):
        """Test query for list of choices to one question"""

        filtered_survey = self.survey.query("B2 == 'A2' | B2 ==  'A5'")

        np.testing.assert_equal(list(filtered_survey.responses.index), [28, 38, 39])

    def test_list_questions(self):
        """Test query for list of choices to one question"""

        filtered_survey = self.survey.query(
            "A11 == 'A1' & (B9b_SQ001 == 'Y' | B9b_SQ002 == 'Y')"
        )

        np.testing.assert_equal(list(filtered_survey.responses.index), [5, 21, 46])


class TestLimeSurveyFilterNa(BaseTestLimeSurvey2021WithResponsesCase):
    """Test LimeSurvey filter_na method"""

    def test_filter_na(self):
        """Test filter_na method"""

        filtered_survey = self.survey.filter_na("F5a")

        np.testing.assert_equal(
            list(filtered_survey.responses.index), [20, 10, 28, 31, 37]
        )


if __name__ == "__main__":
    unittest.main()
