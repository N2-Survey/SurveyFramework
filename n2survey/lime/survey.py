import os
import re
import warnings
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from n2survey.lime.structure import read_lime_questionnaire_structure

__all__ = ["LimeSurvey"]

default_plot_options = {
    "cmap": "Blues",
    "output_folder": os.path.abspath(os.curdir),
    "figsize": (6, 8),
}


def _get_default_plot_kind(survey: "LimeSurvey", question: str) -> str:
    """Get default plot kind for a column or a group of columns

    Args:
        survey (LimeSurvey): LimeSurvey object
        question (str): Name of the responses column or group of questions

    Returns:
        str: String with plot kind, like "bar", etc.
    """

    raise NotImplementedError()


class LimeSurvey:
    """Base LimeSurvey class"""

    def __init__(
        self,
        structure_file: str,
        cmap=None,
        output_folder: Optional[str] = None,
        figsize: Optional[Tuple[int, int]] = None,
    ) -> None:
        """Get an instance of the Survey

        Args:
            structure_file (str): Path to the structure XML file
            cmap ([type], optional): Default color map to use in plots.
              Defaults to None.
            output_folder (str, optional): Default folder to use for saving outputs
              like images, etc. Defaults to current active directory.
            figsize (Tuple[int, int], optional): Default figure size to use in plots.
              Defaults to (6, 8).
        """
        # Parse XML structure file
        structure_dict = read_lime_questionnaire_structure(structure_file)

        # Get pandas.DataFrame table for the structure
        section_df = pd.DataFrame(structure_dict["sections"])
        section_df = section_df.set_index("id")
        question_df = pd.DataFrame(structure_dict["questions"])
        question_df = question_df.set_index("name")
        question_df["is_contingent"] = question_df.contingent_of_name.notnull()
        self.sections = section_df
        self.questions = question_df

        # Update default plotting options
        self.plot_options = default_plot_options.copy()
        if cmap is not None:
            self.plot_options["cmap"] = cmap
        if output_folder is not None:
            self.plot_options["output_folder"] = output_folder
        if figsize is not None:
            self.plot_options["figsize"] = figsize

    def read_responses(self, responses_file: str) -> None:
        """Read responses CSV file

        Args:
            responses_file (str): Path to the responses CSV file

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

        # Identify columns for survey questions
        first_question = columns.get_loc("datestamp") + 1
        last_question = columns.get_loc("interviewtime") - 1
        question_columns = renamed_columns[first_question : last_question + 1]

        # Split df into question responses and timing info
        question_responses = responses[question_columns]
        system_info = responses.iloc[:, ~renamed_columns.isin(question_columns)]

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

    def get_responses(self, question: str, labels: bool = False) -> pd.DataFrame:
        """Get responses for a given question with or without labels

        Args:
            question (str): Question to get the responses for.
            labels (bool, optional): If the response consists of labels or not (default False).

        Raises:
            ValueError: Unconsistent question types within question groups.
            ValueError: Unknown question types.

        Returns:
            [pd.DataFrame]: The response for the selected question.
        """
        question_group = self.questions[self.questions.question_group == question]
        question_types = np.unique(question_group.type)
        question_responses = self.responses.loc[:, question_group.index]
        if len(question_types) == 0:
            raise KeyError(f'No question {question} found.')
        elif len(question_types) > 1:
            raise ValueError(f'Question {question} has multiple types {question_types}.')
        else:
            question_type = question_types[0]

        # get actual question response
        if question_type == 'single-choice':
            # ASSUME: question_responses consists only one column
            #         in result question_group also consists of only one item
            # create a DataFrame because questions_response is only a Series
            response = pd.DataFrame()
            response[question] = question_responses[question_responses.columns[0]]
        elif question_type == 'multiple-choice':
            # ASSUME: question response consists of multiple columns with
            #         'Y' or NaN as entries.
            response = question_responses.notnull()
        elif question_type == 'free':
            # ASSUME: question_responses consists of only one column with
            #         unlimited options of answers.
            response = question_responses
        elif question_type == 'array':
            # ASSUME: question_responses consists of multiple columns with
            #         each column has the same set of possible choices
            response = question_responses
        else:
            # raise error for unimplemented question types
            raise ValueError(f'Unkown question type {question_type}.')

        # replace labels
        if labels:
            if question_type == 'single-choice':
                # rename column and the column entries
                response = response.rename(columns=dict(question_group.label))
                for col_idx in range(len(response.columns)):
                    response.iloc[:, col_idx] = response.iloc[:, col_idx] \
                        .cat.rename_categories(question_group.choices[col_idx])
            elif question_type == 'multiple-choice':
                # WARNING: If choice has no possible mapping, it will be skipped.
                # rename columns only because entries are True or False
                response = response.rename(
                    columns=dict(
                        [(x, y['Y']) for x, y in question_group.choices.items()
                         if y is not np.nan]
                    )
                )
            elif question_type == 'free':
                # rename only columns because entries are not categorical
                response = response.rename(columns=dict(question_group.label))
            elif question_type == 'array':
                # rename all columns and their entries
                response = response.rename(columns=dict(question_group.label))
                for col_idx in range(len(response.columns)):
                    response.iloc[:, col_idx] = response.iloc[:, col_idx] \
                        .cat.rename_categories(question_group.choices[col_idx])
            else:
                # raise error for unimplemented question types
                raise ValueError(f'Unkown question type {question_type}.')

        return response

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
            # Categorical dtype for all questions with answer options
            if renamed_column in self.questions.index:
                if pd.notnull(self.questions.loc[renamed_column, "choices"]):
                    dtype_dict[column] = "category"

            # Categorical dtype for "startlanguage"
            if "language" in column:
                dtype_dict[column] = "category"

            # Float for all timing info
            if re.search("[Tt]ime", column):
                dtype_dict[column] = "float64"

            # Datetime for all time stamps
            if "date" in column:
                datetime_columns.append(column)

        return dtype_dict, datetime_columns

    def plot(self, question, kind: str = None, **kwargs):
        # Find corresponding question or question group,
        # i.e. column or group of columns
        # TODO: ...

        if kind is None:
            kind = _get_default_plot_kind(self, question)
        else:
            # Check is the chosen plot kind is available
            # for the chosen question
            # TODO: ...
            pass

        # Update **kwargs with default_plot_options, i.e.
        # if the value is not provided in **kwargs, then
        # take it from default_plot_options
        # TODO: ...

        # Call the corresponding plot function
        # TODO: ...

        raise NotImplementedError()

    def get_question(self, question: str) -> pd.DataFrame:
        """Get question structure (i.e. subset from self.questions)

        Args:
            question (str): Name of question or subquestion

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

        return questions_subdf

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
        question_type = question_info.type[0]

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
