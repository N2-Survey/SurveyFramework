import os
import re
import warnings
from typing import Optional, Tuple

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

    def get_label(self, question: str) -> str:
        """Get label for the corresponding column or group of colums

        Args:
            question (str): id of question to retrieve

        Returns:
            dict: dict of label mappings
        """

        question_group = self.questions[self.questions["question_group"] == question]
        if question_group.iloc[0]["type"] == "array":
            # Collect labels from all subquestions if "array" type
            label_dict = {
                index: label
                for index, label in zip(question_group.index, question_group["label"])
            }
            label_dict["question_label"] = question_group.iloc[0]["question_label"]
        else:
            # Collect labels from only first in the group if "single-choice" or "multiple-choice" type
            label_dict = {question: question_group.iloc[0]["label"]}

        return label_dict

    def get_choices(self, question: str) -> str:
        """Get choices for the corresponding column or group of colums

        Args:
            question (str): id of question to retrieve

        Returns:
            dict: dict of choices mappings
        """

        question_group = self.questions[self.questions["question_group"] == question]
        if question_group.iloc[0]["type"] == "multiple-choice":
            # Collect choices from all subquestions if "multiple-choice" type
            choices_dict = {
                index: choices
                for index, choices in zip(
                    question_group.index, question_group["choices"]
                )
            }
        else:
            # Collect choices from only first in the group if "single-choice" or "array" type
            choices_dict = {question: question_group.iloc[0]["choices"]}

        return choices_dict
