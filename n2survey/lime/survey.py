import os
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
        # Read the CSV file
        response = pd.read_csv(responses_file)
        columns = response.columns.to_list()
        new_columns = [column.replace("[", "_").replace("]", "") for column in columns]
        response = response.rename(
            columns={
                column: new_column for column, new_column in zip(columns, new_columns)
            }
        )

        # Validate data structure
        # Drop non-question columns
        # (text-display "questions" not listed in structure xml file but present in data csv)
        non_question_columns = ["D8", "F10"]
        response = response.drop(non_question_columns, axis=1)

        # Insert column for Question A2 (missing due to survey error)
        if "A2" not in response.columns:
            response.insert(
                response.columns.get_loc("A1") + 1, "A2", ["A1"] * response.shape[0]
            )

        # Check for columns not listed in survey structure df
        first_question = response.columns.get_loc("A00")
        last_question = response.columns.get_loc("M1")
        missing_columns = [
            column
            for column in response.columns[first_question:last_question]
            if column not in self.questions.index and "other" not in column
        ]
        if missing_columns:
            print(
                f"There is a mismatch between response structure and survey structure.\n{len(missing_columns)} columns are missing in strucutre df."
            )

        # Pre-process data
        # Cast date/time columns to datetime dtype
        response["submitdate"] = pd.to_datetime(
            response["submitdate"], format="%Y-%m-%d %H:%M:%S"
        )
        response["startdate"] = pd.to_datetime(
            response["startdate"], format="%Y-%m-%d %H:%M:%S"
        )
        response["datestamp"] = pd.to_datetime(
            response["datestamp"], format="%Y-%m-%d %H:%M:%S"
        )

        # Cast single-choice columns to unordered categorical dtype
        single_choice_questions = [
            question
            for question in self.questions.index
            if self.questions.loc[question]["format"] == "single_choice"
        ]
        response[single_choice_questions] = response[single_choice_questions].astype(
            "category"
        )

        # Cast array columns to ordered categorical dtype
        array_questions = [
            question
            for question in self.questions.index
            if self.questions.loc[question]["format"] == "array"
        ]
        response[array_questions] = response[array_questions].astype("category")
        for question in array_questions:
            response[question] = response[question].cat.as_ordered()

        # Cast multiple-choice columns to bool dtype
        multiple_choice_questions = [
            question
            for question in self.questions.index
            if self.questions.loc[question]["format"] == "multiple_choice"
        ]
        response[multiple_choice_questions] = response[
            multiple_choice_questions
        ].notnull()

        self.response = response

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
