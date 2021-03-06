import copy
import os
import re
import string
import warnings
from typing import Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from n2survey.lime.structure import read_lime_questionnaire_structure
from n2survey.lime.transformations import (
    calculate_duration,
    range_to_numerical,
    rate_mental_health,
    rate_satisfaction,
    rate_supervision,
)
from n2survey.plot import (
    comparison_numeric_bar_plot,
    likert_bar_plot,
    multiple_choice_bar_plot,
    multiple_multiple_comparison_plot,
    multiple_simple_comparison_plot,
    simple_comparison_plot,
    single_choice_bar_plot,
)
from n2survey.plot.color_schemes import ColorSchemes

__all__ = ["LimeSurvey", "DEFAULT_THEME", "QUESTION_TYPES"]


DEFAULT_THEME = {
    "context": "notebook",
    "style": "darkgrid",
    "palette": "Blues",
    "font": "sans-serif",
    "font_scale": 1,
    "color_codes": True,
    "rc": {
        "figure.figsize": (12, 12),
    },
}

QUESTION_TYPES = (
    "free",
    "array",
    "single-choice",
    "multiple-choice",
)


# PLOT_KINDS_ = [
#     "multiple choice plot",
#     "likert scale plot",
#     "simple comparison plot",
#     "basic bar plot"
# ]


def _clean_file_name(filename: str) -> str:
    """Clean a file name from forbiden characters"""
    # "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in filename if c in valid_chars)


def _split_plot_kwargs(mixed_kwargs: dict) -> tuple[dict, dict]:
    """Split dict of arguments into theme and non-theme arguments

    Args:
        mixed_kwargs (dict): Initial dict of mixed arguments

    Returns:
        tuple[dict, dict]: Tuple of (<theme arguements>, <non-theme arguments>)
    """
    theme_args = {k: v for k, v in mixed_kwargs.items() if k in DEFAULT_THEME}
    nontheme_args = {k: v for k, v in mixed_kwargs.items() if k not in DEFAULT_THEME}
    return theme_args, nontheme_args


def deep_dict_update(source: dict, update_dict: dict) -> dict:
    """Recursive dictionary update

    Args:
        source (dict): Source dictionary to update
        update_dict (dict): Dictionary with "new" data

    Returns:
        dict: Upated dictionary. Neasted dictionaries are updated recursevely
          Neasted lists are combined.
    """
    for key, val in update_dict.items():
        if isinstance(val, dict):
            tmp = deep_dict_update(source.get(key, {}), val)
            source[key] = tmp
        elif isinstance(val, list):
            source[key] = source.get(key, []) + val
        else:
            source[key] = val
    return source


rng = np.random.default_rng()


class LimeSurvey:
    """Base LimeSurvey class"""

    na_label: str = "No Answer"
    theme: dict = None
    output_folder: str = None
    supported_orgs = ["MPS", "Helmholtz", "Leibniz", "TUM", "N2"]
    additional_questions = {
        "state_anxiety_score": {
            "label": "What is the state anxiety score?",
            "type": "free",
        },
        "state_anxiety_class": {
            "label": "What is the state anxiety class?",
            "type": "single-choice",
            "choices": {
                "A1": "no or low anxiety",
                "A2": "moderate anxiety",
                "A3": "high anxiety",
            },
        },
        "trait_anxiety_score": {
            "label": "What is the trait anxiety score?",
            "type": "free",
        },
        "trait_anxiety_class": {
            "label": "What is the trait anxiety class?",
            "type": "single-choice",
            "choices": {
                "A1": "no or low anxiety",
                "A2": "moderate anxiety",
                "A3": "high anxiety",
            },
        },
        "depression_score": {
            "label": "What is the depression score?",
            "type": "free",
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
        },
        "noincome_duration": {
            "label": "For how long have you been working on your PhD without pay?",
            "type": "free",
        },
        "income_amount": {
            "label": "Right now, what is your monthly net income for your work at your research organization?",
            "type": "free",
        },
        "costs_amount": {
            "label": "How much do you pay for your rent and associated living costs per month in euros?",
            "type": "free",
        },
        "contract_duration": {
            "label": "What was or is the longest duration of your contract or stipend related to your PhD project?",
            "type": "free",
        },
        "holiday_amount": {
            "label": "How many holidays per year can you take according to your contract or stipend?",
            "type": "free",
        },
        "hours_amount": {
            "label": "On average, how many hours do you typically work per week in total?",
            "type": "free",
        },
        "holidaytaken_amount": {
            "label": "How many days did you take off (holiday) in the past year?",
            "type": "free",
        },
        "formal_supervision_score": {
            "label": "What is the formal supervision score?",
            "type": "free",
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
        },
        "direct_supervision_score": {
            "label": "What is the direct supervision score?",
            "type": "free",
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
        },
        "phd_duration_days": {
            "label": "What is the length of PhD in days?",
            "type": "free",
        },
        "phd_duration_months": {
            "label": "What is the length of PhD in months?",
            "type": "free",
        },
        "phd_duration_years": {
            "label": "What is the length of PhD in years?",
            "type": "free",
        },
        "phd_duration_category": {
            "label": "What is the length of PhD",
            "type": "single-choice",
            "choices": {
                "A1": "<12 months",
                "A2": "13-24 months",
                "A3": "25-36 months",
                "A4": "37-48 months",
                "A5": ">48 months",
            },
        },
        "satisfaction_score": {
            "label": "What is the satisfaction score?",
            "type": "free",
        },
        "satisfaction_class": {
            "label": "What is the satisfaction class?",
            "type": "single-choice",
            "choices": {
                "A1": "very satisfied",
                "A2": "satisfied",
                "A3": "neither/nor",
                "A4": "dissatisfied",
                "A5": "very dissatisfied",
            },
        },
    }

    def __init__(
        self,
        structure_file: str = None,
        theme: Optional[dict] = None,
        output_folder: Optional[str] = None,
        org: str = None,
    ) -> None:
        """Get an instance of the Survey

        Args:
            structure_file (str, optional): Path to the structure XML file
            theme (Optional[dict], optional): seaborn theme parameters.
              See `seaborn.set_theme` for the details. By default,
              `n2survey.DEFAULT_THEME` is used.
            output_folder (Optional[str], optional): A path to a folder where outputs,
            i.e. plots, repotrs, etc. will be saved. By default, current woring
            directory is used.
            org (str, optional): Name of the organization.
        """

        # Store path to structure file
        if structure_file:
            self.structure_file = os.path.abspath(structure_file)
            self.read_structure(self.structure_file)

        # Update default plotting options
        self.theme = DEFAULT_THEME.copy()
        if theme:
            self.theme.update(theme)

        # Initialize the colorschemes
        ColorSchemes()

        # Set a folder for output results
        self.output_folder = output_folder or os.path.abspath(os.curdir)

        # Store organization information
        if org is not None:
            self._validate_org(org)
            self.theme.update({"palette": org})
        self.org = org

    def set_org(self, org):
        """Set organization attribute

        Args:
            org (str): organization name
        """

        self._validate_org(org)
        self.org = org

    def _validate_org(self, org):
        """Validate organization is among supported ones

        Args:
            org (str): organization name

        Raises:
            AssertionError: org from user input not supported
        """

        if org not in self.supported_orgs:
            raise AssertionError(
                f"Only the following organizations are supported: {self.supported_orgs}"
            )

    def read_structure(self, structure_file: str) -> None:
        """Read structure XML file

        Args:
            structure_file (str): Path to the structure XML file
        """

        # Parse XML structure file
        self.structure_file = os.path.abspath(structure_file)
        structure_dict = read_lime_questionnaire_structure(structure_file)

        # Get pandas.DataFrame table for the structure
        section_df = pd.DataFrame(structure_dict["sections"])
        section_df = section_df.set_index("id")
        question_df = pd.DataFrame(structure_dict["questions"])
        question_df = question_df.set_index("name")
        question_df["is_contingent"] = question_df.contingent_of_name.notnull()
        self.sections = section_df
        self.questions = question_df

        for question, info in self.additional_questions.items():
            self.add_question(question, **info)

    def read_responses(
        self,
        responses_file: str,
        transformation_questions: dict = {},
        org: str = None,
    ) -> None:
        """Read responses CSV file

        Args:
            responses_file (str): Path to the responses CSV file
            transformation_questions (dict, optional): Dict of questions
                requiring transformation of raw data, e.g. {'depression': 'D3'}
                or {'supervision': ['E7a', 'E7b']}
            org (str): organization name

        """

        # Read 1st line of the csv file
        response = pd.read_csv(responses_file, nrows=1, index_col=0)

        # Prepare dtype info
        columns = response.columns
        renamed_columns = (
            columns.str.replace("[", "_", regex=False)
            .str.replace("]", "", regex=False)
            .str.replace("_other", "other", regex=False)
        )
        dtype_dict, datetime_columns = self._get_dtype_info(columns, renamed_columns)

        # Read entire csv with optimal dtypes
        responses = pd.read_csv(
            responses_file,
            index_col=0,
            dtype=dtype_dict,
            parse_dates=datetime_columns,
            infer_datetime_format=True,
        )
        responses = responses.rename(columns=dict(zip(columns, renamed_columns)))

        if "datestamp" in columns:
            # CSV file is unprocessed data
            raw_data = True

            # Identify columns for survey questions
            first_question = columns.get_loc("datestamp") + 1
            last_question = columns.get_loc("interviewtime") - 1
            question_columns = renamed_columns[first_question : last_question + 1]

            # Split df into question responses and timing info
            question_responses = responses.loc[:, question_columns]
            system_info = responses.iloc[:, ~renamed_columns.isin(question_columns)]

        else:
            # CSV file is previously processed data
            raw_data = False
            question_responses = responses
            system_info = pd.DataFrame()
            if org is None:
                org = responses["organization"].iloc[0]
                if pd.isna(org):
                    raise ValueError(
                        "No organization name found in imported data. Please specify."
                    )
                else:
                    self.set_org(org)
            else:
                self.set_org(org)

        # Set correct categories for categorical fields
        for column in self.questions.index:
            choices = self.questions.loc[column, "choices"]
            if (column in question_responses.columns) and pd.notnull(choices):
                question_responses.loc[:, column] = (
                    question_responses.loc[:, column]
                    # We expect all categorical column to be category dtype already
                    # .astype("category")
                    .cat.set_categories(choices.keys())
                )

        if raw_data:
            # Add missing columns for multiple-choice questions with contingent question
            # A contingent question of a multiple-choice question typically looks like this:
            # <response varName="B1T">
            # <fixed>
            #  <category>
            #    <label>Other</label>
            #   <value>Y</value>
            #   <contingentQuestion varName="B1other">
            #    <text>Other</text>
            #     ...
            # For some reason, LimeSurvey does not export values for the parent <response> (B1T in this case).
            # So, here we add those columns artificially based on the contingent question values.
            multiple_choice_questions = self.questions.index[
                (self.questions["type"] == "multiple-choice")
                & self.questions["contingent_of_name"].notnull()
            ]
            for question in multiple_choice_questions:
                question_responses.insert(
                    question_responses.columns.get_loc(question),
                    self.questions.loc[question, "contingent_of_name"],
                    # Fill in new column based on "{question_id}other" column data
                    pd.Categorical(
                        question_responses[question].where(
                            question_responses[question].isnull(), "Y"
                        )
                    ),
                )

        # Validate data structure
        # Check for columns not listed in survey structure df
        not_in_structure = list(
            set(question_responses.columns) - set(self.questions.index)
        )
        if not_in_structure:
            warnings.warn(
                f"The following columns in the data csv file are not found in the survey structure and are dropped:\n{not_in_structure}"
            )
            question_responses = question_responses.drop(not_in_structure, axis=1)
        # Ceheck for questions not listed in data csv
        not_in_data = list(set(self.questions.index) - set(question_responses.columns))
        if not_in_structure:
            warnings.warn(
                f"The following questions in the survey structure are not found in the data csv file:\n{not_in_data}"
            )

        self.responses = question_responses
        self.lime_system_info = system_info

        for transform, questions in transformation_questions.items():
            if not isinstance(questions, list):
                questions = [questions]
            for question in questions:
                self.add_responses(self.transform_question(question, transform))

    def transform_question(self, question: Union[str, tuple], transform: str):
        """Perform transformation on responses to given question

        Args:
            question (str or tuple of str): Question(s) to transform
            transform (str): Type of transform to perform

        Returns:
            pd.DataFrame: Transformed DataFrame to be concatenated to self.responses
        """

        transform_dict = {
            "state_anxiety": "mental_health",
            "trait_anxiety": "mental_health",
            "depression": "mental_health",
            "supervision": "supervision",
            "range": "range_to_numerical",
            "duration": "duration",
            "satisfaction": "satisfaction",
        }

        if transform_dict.get(transform) == "mental_health":
            return rate_mental_health(
                question_label=self.get_label(question + "_SQ001"),
                responses=self.get_responses(question, labels=False),
                choices=self.get_choices(question),
                condition=transform,
            )
        elif transform_dict.get(transform) == "supervision":
            return rate_supervision(
                question_label=self.get_label(question),
                responses=self.get_responses(question, labels=False),
                choices=self.get_choices(question),
            )
        elif transform_dict.get(transform) == "range_to_numerical":
            return range_to_numerical(
                question_label=self.get_label(question),
                responses=self.get_responses(question),
            )
        elif transform_dict.get(transform) == "duration":
            # given in the form of ((start_month,start_year),(end_month,end_year))
            start, end = question
            start_month, start_year = start
            end_month, end_year = end
            return calculate_duration(
                start_month_responses=self.get_responses(start_month, labels=True),
                start_year_responses=self.get_responses(start_year, labels=True),
                end_month_responses=self.get_responses(end_month, labels=True),
                end_year_responses=self.get_responses(end_year, labels=True),
            )
        elif transform_dict.get(transform) == "satisfaction":
            return rate_satisfaction(
                question_label=self.get_label(question),
                responses=self.get_responses(question, labels=False),
                choices=self.get_choices(question),
            )

    def __copy__(self):
        """Create a shallow copy of the LimeSurvey instance

        Returns:
            LimeSurvey: a shallow copy of the LimeSurvey instance
        """
        survey_copy = LimeSurvey()
        survey_copy.__dict__.update(self.__dict__)

        return survey_copy

    def __deepcopy__(self, memo_dict={}):
        """Create a deep copy of the LimeSurvey instance

        Returns:
            LimeSurvey: a deep copy of the LimeSurvey instance
        """

        survey_copy = LimeSurvey()
        survey_copy.__dict__.update(self.__dict__)
        survey_copy.responses = copy.deepcopy(self.responses, memo_dict)

        return survey_copy

    def get_responses(
        self,
        question: str,
        labels: bool = True,
        drop_other: bool = False,
    ) -> pd.DataFrame:
        """Get responses for a given question with or without labels

        Args:
            question (str): Question to get the responses for.
            labels (bool, optional): If the response consists of labels or not (default True).
            drop_other (bool, optional): Whether to exclude contingent question (i.e. "other")

        Raises:
            ValueError: Inconsistent question types within question groups.
            ValueError: Unknown question types.

        Returns:
            [pd.DataFrame]: The response for the selected question.
        """
        question_group = self.get_question(question, drop_other=drop_other)
        question_type = self.get_question_type(question)

        responses = self.responses.loc[:, question_group.index]

        # convert multiple-choice responses
        if question_type == "multiple-choice":
            # ASSUME: question response consists of multiple columns with
            #         'Y' or NaN as entries.
            # Masked with boolean values the responses with nan only for the columns where is_contingent is True.
            # Left-hand-side slicing changed from .loc to __getitem__ to avoid categorical assignment error
            # Reason unclear, see: https://stackoverflow.com/questions/71905655/pandas-can-assign-1-column-
            # dataframe-to-series-but-not-to-dataframe-of-same-sha
            responses[
                question_group.index[~question_group.is_contingent]
            ] = responses.loc[:, ~question_group.is_contingent].notnull()

        # replace labels
        if labels:
            if question_type == "multiple-choice":
                # If a multiple-choice subquestion
                if "SQ" in question:
                    question = question.split("_")[0]
                # Get column labels for entire question group as dict
                rename = self.get_choices(question)
                # Rename column names
                responses = responses.rename(columns=rename)

            else:
                # Rename category values and replace NA by self.na_label
                for column in responses.columns:
                    choices = question_group.loc[column, "choices"]
                    if pd.notnull(choices):
                        responses.loc[:, column] = (
                            responses.loc[:, column]
                            .cat.rename_categories(choices)
                            .cat.add_categories(self.na_label)
                            .fillna(self.na_label)
                        )
                # Rename column names
                responses = responses.rename(columns=dict(question_group.label))

        return responses

    def __getitem__(
        self, key: Union[pd.Series, pd.DataFrame, str, list, tuple]
    ) -> "LimeSurvey":
        """Retrieve or slice the responses DataFrame

        Args:
            key (pd.Series, pd.DataFrame, str, list, or tuple): A key for
                DataFrame slicing or get_responses method

        Returns:
            LimeSurvey: A copy of LimeSurvey instance with filtered responses
                DataFrame
        """
        filtered_survey = self.__copy__()

        # A bool-valued Series, e.g. survey[survey.responses["A3"] == "A5"]
        # is interpreted as a row filter
        if isinstance(key, (pd.Series, pd.DataFrame)):
            filtered_survey.responses = filtered_survey.responses[key]
        # A question id as string, e.g. survey["A3"]
        # is interpreted as a column filter
        elif isinstance(key, str):
            filtered_survey = filtered_survey[[key]]
        # A list of columns, e.g. survey[["C3_SQ001", "C3_Sq002"]]
        # is interpreted as a column filter
        elif isinstance(key, list):
            columns = [
                column
                for question in key
                for column in filtered_survey.get_question(question).index.to_list()
            ]
            filtered_survey.responses = filtered_survey.responses[columns]
        # Two args, e.g. survey[survey.responses["A3"] == "A5", "B1"]
        # or survey[1:10, ["B1", "C1_SQ001"]]
        # is interpreted as (row filter, column filter)
        elif isinstance(key, tuple) and len(key) == 2:
            rows, columns = key
            filtered_survey = filtered_survey[rows]
            filtered_survey = filtered_survey[columns]
        else:
            raise SyntaxError(
                """
                Input must be of type pd.Series, pd.DataFrame, str, list, or tuple.
                Examples:
                    pd.Series or pd.DataFrame: survey[survey.responses["A3"] == "A5"]
                    str: survey["A3"]
                    list of str: survey[["C3_SQ001", "C3_Sq002"]]
                    tuple: survey[survey.responses["A3"] == "A5", "B1"]
                """
            )

        return filtered_survey

    def query(self, expr: str) -> "LimeSurvey":
        """Filter responses DataFrame with a boolean expression

        Args:
            expr (str): Condition str for pd.DataFrame.query().
                E.g. "A6 == 'A3' & "B2 == 'A5'"

        Returns:
            LimeSurvey: LimeSurvey with filtered responses
        """

        # Make copy of LimeSurvey instance
        filtered_survey = self.__copy__()
        # Filter responses DataFrame
        filtered_survey.responses = self.responses.query(expr)

        return filtered_survey

    def filter_na(self, question: str) -> "LimeSurvey":
        """Filter out entries in responses DataFrame with no answer
        to specified question.

        Args:
            question (str): Question to which the entries are filtered.

        returns:
            LimeSurvey: LimeSurvey with filtered responses.
        """

        # Make copy of LimeSurvey instance
        filtered_survey = self.__copy__()
        # Filter responses DataFrame
        filtered_survey.responses = filtered_survey.responses[
            filtered_survey.responses[question].notna()
        ]

        return filtered_survey

    def count(
        self,
        question: str,
        responses: pd.DataFrame = None,
        labels: bool = True,
        dropna: bool = False,
        add_totals: bool = False,
        percents: bool = False,
    ) -> pd.DataFrame:
        """Get counts for a question or a single column

        Args:
            question (str): Name of a question group or a sinlge column
            responses (pd.Dataframe, optional): dataframe to be used instead of `question`
            labels (bool, optional): Use labels instead of codes. Defaults to True.
            dropna (bool, optional): Do not count empty values. Defaults to False.
            add_totals (bool, optional): Add a column and a row with totals. Values
              set to NA if they do not make sense. For example, sums by row for
              multiple choice field. Defaults to False.
            percents (bool, optional): Output percents instead of counts.
              Calculted with respent to the total number of repondents.
              Defaults to False.

        Raises:
            AssertionError: Unexpected question type

        Returns:
            pd.DataFrame: Counts for a given question/column.
              * For question with choices, counts are ordered accordingly and
              catigories that did not occur it responses added with 0 count.
              * For an array question, it is an 2D counts where values are presented
              in the row index and sub_questions are presented in columns.
              * For a multiple-choice question, for each choice, number of respondents
              that chose the correspoinding choise is counted.
              * If `add_totals` is true, then the data frame has one additional column
              and one additional row. Both called "Total" and contains totals or, if
              total count contains misleading data, NA
        """
        if responses is None:
            question_type = self.get_question_type(question)
            responses = self.get_responses(question, labels=labels, drop_other=True)
        else:
            responses = responses

        if responses.shape[1] == 1:
            # If it consist of only one column, i.e. free, single choice, or
            # single column
            counts_df = pd.DataFrame(
                responses.iloc[:, 0].value_counts(dropna=dropna, sort=False)
            )
            # If it is not categorical field, i.e. integer, date, string
            # then sort by values
            if responses.iloc[:, 0].dtype.name != "category":
                counts_df = counts_df.sort_index()
        else:
            if question_type == "multiple-choice":
                counts_df = pd.DataFrame(
                    responses.sum(axis=0), columns=[self.get_label(question)]
                )
            elif question_type == "array":
                counts_df = responses.apply(
                    lambda x: x.value_counts(dropna=dropna, sort=False), axis=0
                )
            else:
                # "free" and "single-choice" are supposed to have be handled before
                # since they consist of only one column
                raise AssertionError(f"Unexpected question type {question}")

        # Add totals
        # Adding totals appends one column and one row with totals
        # per row and per column correspondingly. However, in somecases
        # this summing does not make a sence. Then, we replace those values
        # by NA.
        if add_totals:
            # Add sums per rows and columns
            counts_df = counts_df.append(
                pd.DataFrame(counts_df.sum(axis=0), columns=["Total"]).transpose()
            )
            counts_df.insert(counts_df.shape[1], "Total", counts_df.sum(axis=1))
            # Correct for each question type
            if question_type == "multiple-choice":
                # Sums by row should be equal to number of responses
                counts_df.iloc[:, -1] = responses.shape[0]
                # Sums by column do not make sense, so we replace them by NA
                counts_df.iloc[-1, :] = pd.NA
            elif question_type == "array":
                # Sums by column do not make sense, so we replace them by NA
                counts_df.iloc[:, -1] = pd.NA
            else:
                # For single column questions we can keeps sums by row and by column
                pass

        # Convert to percents
        # We use total number of responses for counting percents
        # to make it consistent between different question types and
        # function argument values
        if percents:
            counts_df = np.round(100 * counts_df / responses.shape[0], 1)

        return counts_df

    def _get_dtype_info(self, columns, renamed_columns):
        """Get dtypes for columns in data csv

        Args:
            columns (list): List of column names from data csv
            renamed_columns (list): List of column names modified to match self.questions entries

        Returns:
            dict: Dictionary of column names and dtypes
            list: List of datetime columns
        """

        # Compile dict with dtype for each column
        dtype_dict = {}
        # Compile list of datetime columns (because pd.read_csv takes this as separate arg)
        datetime_columns = []

        for column, renamed_column in zip(columns, renamed_columns):
            # First try to infer dtype from XML structure information
            if renamed_column in self.questions.index:
                response_format = self.questions.loc[renamed_column, "format"]
                # Categorical dtype for all questions with answer options
                if pd.notnull(self.questions.loc[renamed_column, "choices"]):
                    dtype_dict[column] = "category"
                elif response_format == "date":
                    dtype_dict[column] = "str"
                    datetime_columns.append(column)
                elif response_format == "integer":
                    dtype_dict[column] = pd.Int32Dtype()
                elif response_format == "longtext":
                    dtype_dict[column] = "str"
                else:
                    # Do not include dtype
                    pass
            # Technical fields of limesurvey (Timing, Langueage, etc.)
            else:
                if column == "id":
                    dtype_dict[column] = pd.UInt32Dtype()
                elif column == "submitdate":
                    dtype_dict[column] = "str"
                    datetime_columns.append(column)
                elif column == "lastpage":
                    dtype_dict[column] = pd.Int16Dtype()
                elif column == "startlanguage":
                    dtype_dict[column] = "category"
                elif column == "seed":
                    dtype_dict[column] = pd.UInt32Dtype()
                elif column == "startdate":
                    dtype_dict[column] = "str"
                    datetime_columns.append(column)
                elif column == "datestamp":
                    dtype_dict[column] = "str"
                    datetime_columns.append(column)
                # Float for all timing info
                elif re.search("[Tt]ime", column):
                    dtype_dict[column] = "float64"
                else:
                    # Do not include dtype
                    pass

        return dtype_dict, datetime_columns

    def plot(
        self,
        question,
        compare_with: str = None,
        add_questions: list = [],
        bar_width: float = 0.8,
        totalbar: bool = False,
        suppress_answers: list = [],
        ignore_no_answer: bool = True,
        threshold_percentage: float = 0.0,
        bar_positions: list = [],
        legend_columns: int = 2,
        plot_title: Union[str, bool] = True,
        plot_title_position: tuple = (()),
        plot_title_org: bool = False,
        save: Union[str, bool] = False,
        file_format: str = "png",
        dpi: Union[str, float] = "figure",
        answer_sequence: list = [],
        legend_title: Union[str, bool] = None,
        legend_sequence: list = [],
        calculate_aspect_ratio: bool = True,
        maximum_length_x_axis_answers: int = 20,
        show_zeroes: bool = True,
        bubbles: Union[bool, float] = None,
        kind: str = None,
        **kwargs,
    ):
        """
        Plot answers of the 'question' given.
        Optional Parameters:
            'compare_with':
                correlates answers of 'question' with answers
                of the question given to the 'compare_with' variable.

                'legend_columns':
                    number of columns of the legend added by 'compare_with' on
                    top of the Plot
                    ATTENTION: if the number of columns is too high this will
                    press the plot right next to the legend and smush it.
                'legend_title': if False: no legend-title,
                    if 'True': 'compare_with' question as title,
                    if string: string as legend title
                'legend_sequence': define the order of the legend if you want,
                    else the sequence is the same as the question answers.
            'bar_width':
                define width of the bars in barplots
            'totalbar':
                calculates different total bars, depending on question- and
                comparison-types
            'add_questions':
                adds bars of other questions to the plot
            'suppress_answers':
                removes every entry in 'suppress_answers' from the plot
            'threshold_percentage':
                removes percentages if below threshold, standard is 0
            'bar_positions':
                positions the entries in the plot [0,1.5,2.5,3.5] will assign
                the first 4 answers in the plot (including totalbar) at
                the given positions. Every additional question-position is
                calculated by adding +1 to the highest position, except if the
                answer is the first one of a question in 'add_questions', then
                it automatically adds +1.5 to distinguish the new question from
                the previous one
            'plot_title': if False: no title, if True: question as title,
                if string: string as title
            'plot_title_position': tuple (x,y), if empty, position of the
                title is calculated depending on number of legend entries
                and 'legend_columns'
            'plot_title_org': whether to display organization name in title
            'save': save plot as png or pdf either with question indicator as
                name if True or as string if string is added here.
                Ending of String determines file_format.
                'file_format': if you want to save the file as .pdf rather
                    then as png
                'dpi': Resolution in dotsperinch for saved file, if you want to
                    specify. If not, the resolution is taken from the figure
                    resolution only applies to .png, not to .pdf

            'answer_sequence': getting the answers in the right order made the
                inclusion of an answer_sequence variable necessary, which also
                can be used if you want to give the order of bars yourself,
                just add in a list with the answers as entries in the order you
                want

            'calculate_aspect_ratio': True or False, if False, aspect ratio is
                taken from theme, if True aspect ratio of picture is calculated
                from number of bars and 'bar_width'
            'maximum_length_x_axis_answers': parameter for word wrapping of the
                answers plotted on x-axis, standard 20 --> no line longer then
                20 characters
            'show_zeroes': Plots lines for every 0% bar
            'bubbles': if float or True is given, plots are changed to a bubble
                plot with answers to 'question' and 'add_questions' on the
                x-Axis and answers to 'compare_with' on the y-Axis.
                size of the bubbles depends on overleap percentage and the
                base-value given in bubble_size or on the float given.
        """
        if kind is not None:
            raise NotImplementedError(
                "Forced plot type is not supported yet."
                f"Please use matplotlib directly with"
                f"`servey.get_responses({question})` or `servey.count({question})`"
            )
        # check if plot is implemented:
        self.check_plot_implemented(
            question, compare_with=compare_with, add_questions=add_questions
        )
        # Prepare theme and non-theme arguments
        theme = self.theme.copy()
        theme_kwargs, non_theme_kwargs = _split_plot_kwargs(kwargs)
        theme = deep_dict_update(theme, theme_kwargs)

        question_type = self.get_question_type(question)
        # get plot title
        if plot_title is True:
            plot_title = self.get_label(question)
            if plot_title_org:
                if self.org is None:
                    raise ValueError(
                        f"Must specify organization name as one of {self.supported_orgs}"
                    )
                else:
                    plot_title = f"{self.org}: {plot_title}"
        if compare_with:
            fig, ax = self.plot_comparison(
                question,
                compare_with,
                question_type,
                theme,
                add_questions=add_questions,
                totalbar=totalbar,
                suppress_answers=suppress_answers,
                ignore_no_answer=ignore_no_answer,
                threshold_percentage=threshold_percentage,
                bar_positions=bar_positions,
                legend_columns=legend_columns,
                plot_title=plot_title,
                plot_title_position=plot_title_position,
                answer_sequence=answer_sequence,
                legend_title=legend_title,
                legend_sequence=legend_sequence,
                calculate_aspect_ratio=calculate_aspect_ratio,
                maximum_length_x_axis_answers=maximum_length_x_axis_answers,
                show_zeroes=show_zeroes,
                bubbles=bubbles,
                **kwargs,
            )
        elif question_type == "single-choice":
            counts_df = self.count(question, labels=True)
            fig, ax = single_choice_bar_plot(
                x=counts_df.index.values,
                y=pd.Series(counts_df.iloc[:, 0], name="Number of Responses"),
                plot_title=plot_title,
                theme=theme,
                **non_theme_kwargs,
            )
        elif question_type == "multiple-choice":
            counts_df = self.count(
                question, labels=True, percents=True, add_totals=True
            )
            counts_df.loc[:, "Total"] = self.responses.shape[0]
            counts_df.iloc[-1, :] = np.nan
            counts_df.iloc[:, 0] = counts_df.iloc[:, 0].astype("float64")
            fig, ax = multiple_choice_bar_plot(
                counts_df, theme=theme, plot_title=plot_title, **non_theme_kwargs
            )
        elif question_type == "array":

            counts_df = self.count(
                question,
                labels=True,
                percents=False,
                add_totals=True,
            )
            counts_df.loc["Total", "Total"] = self.responses.shape[0]
            fig, ax = likert_bar_plot(
                counts_df,
                theme=theme,
                bar_spacing=0.2,
                bar_thickness=0.4,
                group_spacing=1,
                calc_fig_size=True,
                plot_title=plot_title,
                **non_theme_kwargs,
            )
            plt.tight_layout()

        # Save to a file
        if save:
            self.save_plot(
                fig,
                question,
                compare_with=compare_with,
                add_questions=add_questions,
                save=save,
                file_format=file_format,
                dpi=dpi,
            )
        return fig, ax

    def plot_comparison(
        self,
        question,
        compare_with,
        question_type,
        theme,
        add_questions: list = [],
        bar_width: float = 0.8,
        totalbar: bool = False,
        suppress_answers: list = [],
        ignore_no_answer: bool = True,
        threshold_percentage: float = 0.0,
        bar_positions: list = [],
        legend_columns: int = 2,
        plot_title: Union[str, bool] = True,
        plot_title_position: tuple = (()),
        answer_sequence: list = [],
        legend_title: Union[str, bool] = None,
        legend_sequence: list = [],
        calculate_aspect_ratio: bool = True,
        maximum_length_x_axis_answers: float = 20,
        kind: str = None,
        show_zeroes: bool = True,
        bubbles: Union[bool, float] = None,
        **kwargs,
    ):
        """
        outsourcing of plot_comparison() from plot(), because flake8 says to
        complicated, for keyword explanation please see plot() function
        """
        # load necessary data for comparison
        compare_with_type = self.get_question_type(compare_with)
        if legend_title is True:
            legend_title = self.get_label(compare_with)
        if not legend_sequence:
            legend_sequence = list(
                self.count(compare_with, labels=True).index.values.astype(str)
            )
        if not answer_sequence:
            answer_sequence = self.get_answer_sequence(
                question, add_questions=add_questions, totalbar=totalbar
            )
        plot_data_list = self.create_comparison_data(
            question, compare_with, add_questions=add_questions
        )
        # create total bar data if needed
        if totalbar:
            totalbar_data = self.create_total_bar_data(
                question_type=question_type, compare_with=compare_with
            )
        else:
            totalbar_data = None
        if question_type == "single-choice":
            print("single-single")
            fig, ax = simple_comparison_plot(
                plot_data_list,
                totalbar=totalbar_data,
                suppress_answers=suppress_answers,
                ignore_no_answer=ignore_no_answer,
                bar_positions=bar_positions,
                threshold_percentage=threshold_percentage,
                legend_columns=legend_columns,
                plot_title=plot_title,
                plot_title_position=plot_title_position,
                legend_title=legend_title,
                answer_sequence=answer_sequence,
                legend_sequence=legend_sequence,
                theme=theme,
            )
        elif all(
            [question_type == "multiple-choice", compare_with_type == "single-choice"]
        ):
            print("multi-single")
            fig, ax = multiple_simple_comparison_plot(
                plot_data_list,
                totalbar=totalbar_data,
                bar_width=bar_width,
                suppress_answers=suppress_answers,
                ignore_no_answer=ignore_no_answer,
                bar_positions=bar_positions,
                threshold_percentage=threshold_percentage,
                legend_columns=legend_columns,
                plot_title=plot_title,
                plot_title_position=plot_title_position,
                legend_title=legend_title,
                answer_sequence=answer_sequence,
                legend_sequence=legend_sequence,
                calculate_aspect_ratio=calculate_aspect_ratio,
                maximum_length_x_axis_answers=maximum_length_x_axis_answers,
                theme=theme,
                show_zeroes=show_zeroes,
                bubbles=bubbles,
            )
        elif all(
            [question_type == "multiple-choice", compare_with_type == "multiple-choice"]
        ):
            print("multi-multi")
            fig, ax = multiple_multiple_comparison_plot(
                plot_data_list,
                totalbar=totalbar_data,
                bar_width=bar_width,
                suppress_answers=suppress_answers,
                ignore_no_answer=ignore_no_answer,
                bar_positions=bar_positions,
                threshold_percentage=threshold_percentage,
                legend_columns=legend_columns,
                plot_title=plot_title,
                plot_title_position=plot_title_position,
                legend_title=legend_title,
                answer_sequence=answer_sequence,
                legend_sequence=legend_sequence,
                calculate_aspect_ratio=calculate_aspect_ratio,
                maximum_length_x_axis_answers=maximum_length_x_axis_answers,
                theme=theme,
                show_zeroes=show_zeroes,
                bubbles=bubbles,
            )
        return fig, ax

    def plot_numeric_comparison(
        self,
        question,
        questions_to_filter,
        simple_filtering: bool = True,
        valid_questions: list = None,
        display_title: bool = True,
        display_unfiltered_data: bool = True,
        display_no_answer: bool = True,
        display_median: bool = False,
        display_percents: bool = False,
        fig_size_inches: tuple = None,
        save: bool = False,
        **kwargs,
    ):
        """Plot comparison plots for numeric questions (with filtering).

        Args:
            question (str): Name of numeric question (for which filtering will be done)
            questions_to_filter (dict): Dictionary of non-numeric questions with which `question` will
                                        be filtered, e.g. {"A6": ["A1", "A3"]}, {"A6": "all"}/{"A6": ["all"]}
            simple_filtering (bool, optional): Each entry of `questions_to_filter` is used for
                                               individual filtering. Otherwise up to two entries will be
                                               filtered simultaneously. Defaults to True.
            valid_questions (list, optional): List of valid numeric questions for `question`.
            display_title (bool, optional): Display question as title in resulting plot. Defaults to True.
            display_unfiltered_data (bool, optional): Display distribution of total data (without filtering). Defaults to True.
            display_no_answer (bool, optional): Hide invalid answers. Defaults to True.
            display_median (bool, optional): Display median in each subplot. Defaults to True.
            display_percents (bool, optional): Display percentages in each subplot. Defaults to False
            fig_size_inches (tuple): Size of the resulting figure. Defaults to None.
            save (bool, optional): Save the resulting figure. Defaults to True.

        Raises:
            NotImplementedError: - `question` NOT numeric single-choice
                                 - `questions_to_filter` ARE numeric questions,
                                    HAVE invalid keys or HAVE invalid values
        """
        # Prepare theme and non-theme arguments
        theme = self.theme.copy()
        theme_kwargs, non_theme_kwargs = _split_plot_kwargs(kwargs)
        theme = deep_dict_update(theme, theme_kwargs)

        # Set up question as title for figure
        if display_title:
            title = self.get_label(question)
        else:
            title = None

        # Define valid numeric questions
        if valid_questions is None:
            valid_questions = ["B1b", "B2", "B3", "B4", "B10", "C4", "C8"]

        # Check if `question` is numeric single-choice question
        question_type = self.get_question_type(question)
        if question_type != "single-choice" or question not in valid_questions:
            raise NotImplementedError(
                "Comparison plot is only implemented for numeric single-choice questions."
                f"{question} is not a numeric single-choice question."
            )

        # Check if `questions_to_filter`: - are NOT numerical questions &
        #                                 - have only single-choice questions as keys &
        #                                 - have valid answer possibilites as values.
        for key, values in questions_to_filter.items():
            questions_to_filter_type = self.get_question_type(key)
            if questions_to_filter_type != "single-choice" or key in valid_questions:
                raise NotImplementedError(
                    "Comparison plot is only implemented for single-choice non-numeric questions."
                    f"{key} is either not a single-choice question or a numeric question."
                )
            possible_answers = list(self.questions.loc[key, "choices"])
            if "-oth-" in possible_answers:
                possible_answers.remove("-oth-")
            # If `all` is specified {"A6": "all"}/{"A6": ["all"]}, use all answer possibilities
            if "all" in values:
                questions_to_filter[key] = possible_answers
            if not all(
                answer in possible_answers for answer in questions_to_filter[key]
            ):
                raise ValueError(
                    f"Selected answer possibilities ({values}) are not in question {key}!"
                    f"Question {key} has valid possibilties: {possible_answers}!"
                )

        # Preprocess and group data in `question` according to `selected_answers`
        # First find indices to split data and store in list as arrays
        list_of_labels = list()
        list_of_counts_df = list()
        list_of_responses = list()
        # First element is unfiltered data, then filtered data
        unfiltered_responses = self.get_responses(
            question, labels=True, drop_other=True
        )
        unfiltered_counts_df = self.count(question, labels=True)
        list_of_labels.append("Total")
        list_of_counts_df.append(unfiltered_counts_df)
        list_of_responses.append(unfiltered_responses)

        # Simple filtering: Filter `question` according to answers in `questions_to_filter` individually
        if simple_filtering:
            label = "simple"
            for key, values in questions_to_filter.items():
                for value in values:
                    # Get indices and filter array according to these
                    filtered_responses, counts_df = self.filter_responses(
                        question, unfiltered_responses, [key, value]
                    )
                    # Skip comparisons if filtered DataFrame has no counts of valid answers
                    # Last entry corresponds to 'No Answer'
                    if counts_df[:-1].sum(axis=0)[0] > 0:
                        list_of_labels.append(self.get_choices(key)[value])
                        list_of_counts_df.append(counts_df)
                        list_of_responses.append(filtered_responses)

        # Multiple filtering: Filter `question` according to all combinations of answers in `questions_to_filter`
        # e.g. `questions_to_filter`: {'gender': ['male', 'female'],
        #                              'nationality': ['German', 'Non-German']}
        # --> 4 possible combinations: 'male'+'German', 'female'+'German',
        #                              'male'+'Non-German', 'female'+'Non-German'
        else:
            label = "multiple"
            # Multiple comparisons only done for: - max. 2 `questions_to_filter`
            if len(questions_to_filter.keys()) != 2:
                raise NotImplementedError(
                    "When specifying `simple_filtering=False` please provide exactly two `questions_to_filter`!"
                )
            first_key, first_values = list(questions_to_filter.items())[0]
            second_key, second_values = list(questions_to_filter.items())[1]
            # Go through all entries of first element of `questions_to_filter`
            for first_value in first_values:
                for second_value in second_values:
                    filtered_responses, counts_df = self.filter_responses(
                        question,
                        unfiltered_responses,
                        [first_key, first_value],
                        [second_key, second_value],
                    )
                    # Skip comparisons if filtered DataFrame has no counts of valid answers
                    # Last entry corresponds to 'No Answer'
                    if counts_df[:-1].sum(axis=0)[0] > 0:
                        list_of_labels.append(
                            self.get_choices(first_key)[first_value]
                            + " + "
                            + self.get_choices(second_key)[second_value]
                        )
                        list_of_counts_df.append(counts_df)
                        list_of_responses.append(filtered_responses)
        fig, ax = comparison_numeric_bar_plot(
            self,
            question,
            list_of_responses,
            list_of_counts_df,
            list_of_labels,
            display_unfiltered_data=display_unfiltered_data,
            display_no_answer=display_no_answer,
            display_percents=display_percents,
            title=title,
            fig_size_inches=fig_size_inches,
            theme=theme,
            **kwargs,
        )
        # Save to a file
        if save:
            filename = f"Numeric_{label}_comparison_{question}_with_{list(questions_to_filter.keys())}.png"
            filename = _clean_file_name(filename).replace(" ", "_")
            self.save_plot(fig, question, save=filename)

    def filter_responses(self, question, unfiltered_responses, *args):
        """Filtering of responses called in `plot_numeric_comparison`.

        Args:
            question (str): Name of numeric question (for which filtering will be done)
            unfiltered_responses (DataFrame): Unfiltered responses dataframe of `question`
            *args: List(s) originating from `questions_to_filter` like [question, answer]; for
                   multiple filtering: two lists are passed

        Returns:
            filtered_responses (DataFrame): Dataframe of filtered response dataframe
            countes_filtered_responses (DataFrame): Dataframe of counts of filtered response dataframe
        """
        # Simple filtering
        if len(args) == 1:
            key, value = args[0]
            indices, _ = np.where(
                self.get_responses(key, labels=False, drop_other=True) == value
            )
        # Multiple filtering (only works for exactly two filtering options)
        elif len(args) == 2:
            first_key, first_value = args[0]
            second_key, second_value = args[1]
            first_responses = self.get_responses(
                first_key, labels=False, drop_other=True
            )
            second_responses = self.get_responses(
                second_key, labels=False, drop_other=True
            )
            indices, _ = np.where(
                np.logical_and(
                    np.asarray(first_responses) == first_value,
                    np.asarray(second_responses) == second_value,
                )
            )
        filtered_responses = unfiltered_responses.iloc[indices]
        counts_filtered_responses = self.count(
            question, responses=filtered_responses, labels=True
        )
        return filtered_responses, counts_filtered_responses

    def save_plot(
        self,
        fig,
        question,
        compare_with: str = None,
        add_questions: list = [],
        save: Union[str, bool] = False,
        file_format: str = "png",
        dpi: Union[str, float] = "figure",
    ):
        """
        creates 'filename' from 'question' and, if given, 'compare_with' and
        'add_questions' and saves file to output_folder if 'save' is True.
        'save' = string: string replaces savename of plot
        'file_format': can be changed from pixelbased .png to .pdf
        (vector graphics --> loss free scalable)
        'dpi': specifies resolution in dots per inch for .png
        """
        if isinstance(save, str):
            filename = save
        else:
            filename = f"{question}"
            for entry in add_questions:
                filename = filename + f"_{entry}"
            if compare_with:
                filename = filename + f"_vs_{compare_with}"
            filename = f"{self.org}-{filename}.{file_format}"
        filename = _clean_file_name(filename)
        fullpath = os.path.join(self.output_folder, filename)
        fig.savefig(fullpath, dpi=dpi)
        print(f"Saved plot to {fullpath}")
        return True

    def check_plot_implemented(self, question, compare_with=None, add_questions=[]):
        """
        Check if question type and/or combination of questions for
        compare_with is already implemented and working
        """
        supported_plots = ["single-choice", "multiple-choice", "array"]
        supported_comparisons = [
            ("single-choice", "single-choice"),
            ("multiple-choice", "single-choice"),
            ("multiple-choice", "multiple-choice"),
        ]
        all_plots = [question]
        if compare_with:
            all_plots.append(compare_with)
        all_plots = all_plots + add_questions
        question_types = [self.get_question_type(plot) for plot in all_plots]
        count = 0
        for question_type in question_types:
            if question_type not in supported_plots:
                plot = all_plots[count]
                print(f"{plot} is unsupported questiontype")
                raise NotImplementedError(
                    """
                    Question type not yet implemented
                    """
                )
            count = count + 1
        if compare_with:
            tuple_list = [(question, compare_with)]
            for i in add_questions:
                tuple_list.append((question, i))
            for i in tuple_list:
                question_type_tuple = (
                    self.get_question_type(i[0]),
                    self.get_question_type(i[1]),
                )
                if question_type_tuple not in supported_comparisons:
                    raise NotImplementedError(f"Comparison {i} not yet implemented")

    def get_answer_sequence(self, question, add_questions=[], totalbar=False):
        """
        Create answer sequence from given questions to keep sequence in
        plot consistent if answers that were never chosen are suppressed
        """
        answer_sequence = [
            list(self.count(question, labels=True).index.values.astype(str))
        ]
        for entry in add_questions:
            answer_sequence.append(
                list(self.count(entry, labels=True).index.values.astype(str))
            )
        if totalbar:
            answer_sequence[0].insert(0, "Total")
        return answer_sequence

    def create_comparison_data(self, question, compare_with, add_questions=[]):
        """
        Load and combine necessary data for the plot functions.
        depending on the wanted (question/add_question_entry,compare_with) tuple
        """
        plot_data_list = []
        if self.get_question_type(question) == "single-choice":
            if self.get_question_type(compare_with) == "single-choice":
                # create Dataarray from all existing combinations of
                # question and compare_with
                plot_data_list.append(
                    pd.concat(
                        [
                            self.get_responses(question, labels=True, drop_other=True),
                            self.get_responses(
                                compare_with, labels=True, drop_other=True
                            ),
                        ],
                        axis=1,
                    )
                )
            if add_questions:
                # add combinations for additional questions with
                # 'compare_with' question
                for entry in add_questions:
                    if self.get_question_type(compare_with) == "single-choice":
                        next_plot_data = pd.concat(
                            [
                                self.get_responses(entry, labels=True, drop_other=True),
                                self.get_responses(
                                    compare_with, labels=True, drop_other=True
                                ),
                            ],
                            axis=1,
                        )
                        plot_data_list.append(next_plot_data)
        if self.get_question_type(question) == "multiple-choice":
            if self.get_question_type(compare_with) == "single-choice":
                # create Dataarray from all existing combinations of
                # question and compare_with
                plot_data_list.append(
                    (
                        self.get_responses(question, labels=True, drop_other=True),
                        self.get_responses(compare_with, labels=True, drop_other=True),
                    )
                )
            elif self.get_question_type(compare_with) == "multiple-choice":
                # create Dataarray from all existing combinations of
                # question and compare_with
                plot_data_list.append(
                    (
                        self.get_responses(question, labels=True, drop_other=True),
                        self.get_responses(compare_with, labels=True, drop_other=True),
                    )
                )
        return plot_data_list

    def create_total_bar_data(self, question_type, compare_with):
        totalbar_data = np.unique(
            self.get_responses(compare_with, labels=True, drop_other=True),
            return_counts=True,
        )
        return totalbar_data

    def get_question(self, question: str, drop_other: bool = False) -> pd.DataFrame:
        """Get question structure (i.e. subset from self.questions)

        Args:
            question (str): Name of question or subquestion
            drop_other (bool, optional): Whether to exclude contingent question (i.e. "other")
        Raises:
            ValueError: There is no such question or subquestion

        Returns:
            pd.DataFrame: Subset from `self.questions` with corresponding rows
        """

        questions_subdf = self.questions[
            (self.questions["question_group"] == question)
            | (self.questions.index == question)
        ]

        if questions_subdf.empty:
            raise ValueError(f"Unexpected question code '{question}'")

        if drop_other:
            questions_subdf = questions_subdf[~questions_subdf.is_contingent]

        return questions_subdf

    def add_question(
        self, name: str, responses: Union[pd.Series, pd.DataFrame] = None, **kwargs
    ):
        """Add question to self.questions DataFrame

        Args:
            name (str): Name (id) of the question to add, e.g. "A12"
            responses (pd.Series or pd.DataFrame, optional): responses
                to the question to be added
            **kwargs (optional): Attributes of the question to be added,
                e.g. type="single-choice", choices={"A1": "Yes", "A2": "No"}
        """

        # Add "is_contingent" attribute if not specified
        # as this attribute cannot be empty
        if not kwargs.get("is_contingent"):
            kwargs["is_contingent"] = False

        self.questions = pd.concat(
            [self.questions, pd.DataFrame([kwargs], index=[name])]
        )

        # Add responses to self.responses if given
        if responses is not None:
            self.add_responses(responses=responses, question=name)

    def add_responses(
        self,
        responses: Union[pd.Series, pd.DataFrame],
        question: Union[list, str] = None,
    ):
        """Add responses to specified question to self.responses DataFrame

        Args:
            responses (pd.Series or pd.DataFrame): responses to be added
                to self.responses
            question (list or str, optional): Name (id) of question to which
                the responses correspond. If not given, the column/Series name
                is taken as the name
        """

        # Rename the column(s)/Series if question is specified
        if question is not None:
            if isinstance(question, str):
                question = [question]
            if isinstance(responses, pd.DataFrame):
                responses = responses.rename(
                    columns={
                        column: name
                        for column, name in zip(responses.columns, question)
                    }
                )
            if isinstance(responses, pd.Series):
                responses.name = question[0]

        self.responses = pd.concat([self.responses, responses], axis=1)

    def get_question_type(self, question: str) -> str:
        """Get question type and validate it

        Args:
            question (str): question or column code

        Raises:
            AssertionError: Unconsistent question types within question
            AssertionError: Unexpected question type

        Returns:
            str: Question type like "single-choice", "array", etc.
        """

        question_group = self.get_question(question)
        question_types = question_group.type.unique()

        if len(question_types) > 1:
            raise AssertionError(
                f"Question {question} has multiple types {list(question_types)}."
            )

        question_type = question_types[0]
        if question_type not in QUESTION_TYPES:
            raise AssertionError(f"Unexpected question type {question_type}.")

        return question_type

    def get_label(self, question: str) -> str:
        """Get label for the corresponding column or group of colums

        Args:
            question (str): Name of question or subquestion

        Returns:
            str: question label/title
        """

        question_info = self.get_question(question)

        if question_info.shape[0] > 1:
            label = question_info.question_label[0]
        else:
            label = question_info.label[0]

        return label

    def get_choices(self, question: str) -> dict:
        """Get choices of a question

        * For multiple-choice group, format is `<subquestion code: subquestion title>`,
        for example, {"C3_SQ001": "I do not like scientific work.", "C3_SQ002": ...}
        * For all other fixed questions (i.e. array, single choice, subquestion), returns
          choices of that question or column
        * For free and contingent, returns None

        Args:
            question (str): Name of question or subquestion to retrieve

        Returns:
            dict: dict of choices mappings
        """

        question_info = self.get_question(question)
        question_info = question_info[~question_info.is_contingent]
        question_type = self.get_question_type(question)

        # If set of multiple-choice questions
        if (question_info.shape[0] > 1) and (question_type == "multiple-choice"):
            # Flatten nested dict and get choice text directly for multiple-choice
            choices_dict = {
                index: row.choices["Y"] for index, row in question_info.iterrows()
            }
        # If single-choice, free, individual subquestion, or array
        else:
            choices_dict = question_info.choices[0]

        return choices_dict

    def export_to_file(
        self,
        org: str = None,
        drop_columns: Union[str, list] = [],
        rename_columns: dict = {},
        directory: str = None,
        verbose: bool = True,
    ):
        """Export anonymised data for question to file

        Args:
            org (str): Name of the organization to which the
                exported data belong. Optional if org is specified
                in instantiation, but overrides it if given here
            drop_columns (str or list, optional): One or list of columns
                to remove in addition to free inputs
            rename_columns (dict, optional): Dict of columns to rename
            directory (str, optional): File path to which to
                save csv file. Default is the current working directory.
            verbose (bool, optional): Whether to display checks for similarity
                after random permutation. Default is True

        """
        # If no dierctory specified, use current working direction
        if not directory:
            directory = os.getcwd()

        data = self.responses.copy()
        columns_to_drop = []
        # Drop user specified questions
        if drop_columns:
            if isinstance(drop_columns, str):
                drop_columns = [drop_columns]
            nonexistent = set(drop_columns) - set(data.columns)
            if nonexistent:
                raise KeyError(
                    f"The following columns are not found in responses DataFrame: {nonexistent}"
                )
            columns_to_drop = columns_to_drop + drop_columns
        # Drop questions with free input
        columns_to_drop = (
            columns_to_drop
            + self.questions[self.questions["format"] == "longtext"].index.to_list()
        )

        data.drop(columns=columns_to_drop, inplace=True)
        new_data = data.copy()
        # Randomly permute values in each column
        for column in data.columns:
            new_data[column] = rng.permutation(data[column])

        # Display similarity statistics after permutation
        if verbose:
            print(f"There are in total {data.shape[0]} response entries")
            unchanged = data[data == new_data]
            unchanged_rows = unchanged.count(axis="columns") / new_data.shape[1]
            print(
                f"of which {unchanged_rows[unchanged_rows > 0.1].shape[0]} entries after random permutation have at least 10% of columns identical to before."
            )
            print(
                f"Over all entries, the average percentage of columns identical to before permutation is {round(unchanged_rows.mean() * 100)}%."
            )
            unchanged_columns = unchanged.count()
            print(
                f"The top five questions with the most identical entries are \n{unchanged_columns[unchanged_columns > 0].sort_values(ascending=False).head(5)}"
            )

        # Rename columns if dict given
        if rename_columns:
            new_data = new_data.rename(columns=rename_columns)

        # Check org name is given or available from instantiation
        if org is None:
            if self.org is None:
                org = ""
            else:
                org = self.org
        else:
            # Validate org name
            self._validate_org(org)
        new_data.insert(0, "organization", org)

        # Generate file name if not given
        if not directory.endswith(".csv"):
            directory = os.path.join(directory, f"{org}-anonymised-data.csv")

        new_data.to_csv(directory)

        print("\nData exported!")
