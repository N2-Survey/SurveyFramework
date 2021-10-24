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

        # Infer question type from available choices
        for i in range(question_df.shape[0]):
            if question_df.loc[i]["format"] is None:
                if "Y" in question_df.loc[i]["choices"].keys():
                    question_df.loc[i, ["format"]] = "multiple_choice"
                elif "SQ" in question_df.loc[i]["name"]:
                    question_df.loc[i, ["format"]] = "array"
                else:
                    question_df.loc[i, ["format"]] = "single_choice"

        # Correct inconsistency in column names and set index column
        question_df["name"] = question_df["name"].str.replace("T", "_other")
        question_df = question_df.set_index("name")

        # Save structure df to attributes
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

    def read_response(self, responses_file: str) -> None:
        """Read response CSV file

        Args:
            response_file (str): Path to the responses CSV file

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
        first_question = columns.get_loc("A00")
        last_question = columns.get_loc("M1")
        question_columns = renamed_columns[first_question : last_question + 1]

        # Split df into question responses and timing info
        question_responses = responses[question_columns].copy()
        system_info = responses[
            [column for column in renamed_columns if column not in question_columns]
        ].copy()

        # Add missing "{question_id}T" columns for multiple-choice questions, e.g. "B1T"
        multiple_choice_questions = list(
            self.questions.loc[
                (self.questions["type"] == "multiple-choice")
                & (self.questions["format"] == "longtext"),
                "question_group",
            ].unique()
        )
        for question in multiple_choice_questions:
            other_column = question + "other"
            question_responses.insert(
                question_responses.columns.get_loc(other_column),
                question + "T",
                # Fill in new column based on "{question_id}other" column data
                pd.Categorical(
                    question_responses[other_column].where(
                        question_responses[other_column].isnull(), "Y"
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
        self.sys_info = system_info

    def _get_dtype_info(self, columns, renamed_columns):
        """Get dtypes for columns in data csv

        Args:
            columns (list): List of column names from data csv
            renamed_columns (list): List of column names modified to match self.questions entries

        Returns:
            dict: Dictionary of column names and dtypes
            list: List of datetime columns
        """

        # Compile dict with dtype for each column and list of datetime columns
        dtype_dict = {}
        datetime_columns = []
        for column, renamed_column in zip(columns, renamed_columns):
            if renamed_column in self.questions.index:
                if (
                    self.questions.loc[renamed_column, "type"]
                    in ["single-choice", "multiple-choice", "array"]
                    and self.questions.loc[renamed_column, "format"] is None
                ):
                    dtype_dict[column] = "category"
            if "language" in column:
                dtype_dict[column] = "category"
            if re.search("[Tt]ime", column):
                dtype_dict[column] = "float64"
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
        """Get label for the corresponding column or group of colums"""
        raise NotImplementedError()

    def get_choices(self, question: str) -> str:
        """Get choices for the corresponding column or group of colums"""
        raise NotImplementedError()
