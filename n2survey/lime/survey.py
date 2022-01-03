import os
import re
import string
import warnings
from typing import Optional, Union

import numpy as np
import pandas as pd

from n2survey.lime.structure import read_lime_questionnaire_structure
from n2survey.plot import (
    likert_bar_plot,
    multiple_choice_bar_plot,
    single_choice_bar_plot,
)

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


def _clean_file_name(filename: str) -> str:
    """Clean a file name from forbiden characters"""
    # "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    valid_chars = "-_.() %s%s" % (string.ascii_letters, string.digits)
    return "".join(c for c in filename if c in valid_chars)


class LimeSurvey:
    """Base LimeSurvey class"""

    na_label: str = "No Answer"
    theme: dict = None
    output_folder: str = None

    def __init__(
        self,
        structure_file: str,
        theme: Optional[dict] = None,
        output_folder: Optional[str] = None,
    ) -> None:
        """Get an instance of the Survey

        Args:
            structure_file (str): Path to the structure XML file
            theme (Optional[dict], optional): seaborn theme parameters.
              See `seaborn.set_theme` for the details. By default,
              `n2survey.DEFAULT_THEME` is used.
            output_folder (Optional[str], optional): A path to a folder where outputs,
            i.e. plots, repotrs, etc. will be saved. By default, current woring
            directory is used.
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
        self.theme = DEFAULT_THEME.copy()
        if theme:
            self.theme.update(theme)

        # Set a folder for output results
        self.output_folder = output_folder or os.path.abspath(os.curdir)

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
        question_responses = responses.loc[:, question_columns]
        system_info = responses.iloc[:, ~renamed_columns.isin(question_columns)]

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
            ValueError: Unconsistent question types within question groups.
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
            responses = responses.notnull()

        # replace labels
        if labels:
            if question_type == "multiple-choice":
                # Rename column names
                responses = responses.rename(columns=self.get_choices(question))
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

    def count(
        self,
        question: str,
        labels: bool = True,
        dropna: bool = False,
        add_totals: bool = False,
        percents: bool = False,
    ) -> pd.DataFrame:
        """Get counts for a question or a single column

        Args:
            question (str): Name of a question group or a sinlge column
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
        question_type = self.get_question_type(question)
        responses = self.get_responses(question, labels=labels, drop_other=True)

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
        kind: str = None,
        save: Union[str, bool] = False,
        **kwargs,
    ):
        if kind is not None:
            raise NotImplementedError(
                "Forced plot type is not supported yet."
                f"Please use matplotlib directly with"
                f"`servey.get_responses({question})` or `servey.count({question})`"
            )

        # Set up plot options
        theme = self.theme.copy()
        theme.update(kwargs)

        question_type = self.get_question_type(question)

        if question_type == "single-choice":
            counts_df = self.count(question, labels=True)
            fig, ax = single_choice_bar_plot(
                x=counts_df.index.values,
                y=pd.Series(counts_df.iloc[:, 0], name="Number of Responses"),
                title=counts_df.columns[0],
                theme=theme,
            )
        elif question_type == "multiple-choice":
            counts_df = self.count(
                question, labels=True, percents=True, add_totals=True
            )
            counts_df.loc[:, "Total"] = self.responses.shape[0]
            counts_df.iloc[-1, :] = np.nan
            counts_df.iloc[:, 0] = counts_df.iloc[:, 0].astype("float64")
            fig, ax = multiple_choice_bar_plot(
                counts_df,
                theme=theme,
                display_title=True,
                sort="descending",
                bar_spacing=1.2,
            )
        elif question_type == "array":
            display_title = True
            display_no_answer = False

            counts_df = self.count(
                question, labels=True, percents=False, add_totals=True
            )
            counts_df.loc["Total", "Total"] = self.responses.shape[0]
            if not display_no_answer:
                try:
                    counts_df = counts_df.drop("No Answer")
                except KeyError:
                    pass

            if display_title:
                title_question = self.get_label(question)
            else:
                title_question = None

            fig, ax = likert_bar_plot(
                counts_df,
                theme=theme,
                title_question=title_question,
                bar_spacing=0.2,
                bar_thickness=0.4,
                group_spacing=1,
                calc_fig_size=True,
            )
        else:
            raise NotImplementedError(
                "Only single choice fields are available."
                f"Please use matplotlib directly with"
                f"`servey.get_responses({question})` or `servey.count({question})`"
            )

        # Save to a file
        if save:
            filename = f"{counts_df.columns[0]}.png"
            if isinstance(save, str):
                filename = save
            # Make a valid file name
            filename = _clean_file_name(filename)
            fullpath = os.path.join(self.output_folder, filename)
            fig.savefig(fullpath)
            print(f"Saved plot to {fullpath}")

        fig.show()

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

    def export_to_file(self, question, directory=None):
        """Export aggregate data for question to file

        Args:
            question (str): Name of question
            directory (str): Optional, path to directory in which to save csv file. Default is ./data
        """

        data = self.count(question)
        data.to_csv(os.path.join(directory or "./data", question + ".csv"))

    def import_from_file(self, path):
        """Import aggregate data for question from file

        Args:
            path (str): Path to csv file.

        Returns:
            DataFrame: df containing aggregate data for question
        """

        df = pd.read_csv(path, index_col=0)

        return df
