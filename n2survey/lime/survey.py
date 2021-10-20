import os
from typing import Optional, Tuple

import pandas as pd

from n2survey import lime

__all__ = ["LimeSurvey"]


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

    # Deafult options for plotting
    default_plot_options = {
        "cmap": None,
        "figsize": (6, 8),
        "output_folder": os.path.abspath(os.curdir),
    }

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
        structure_dict = lime.read_lime_questionnaire_structure(structure_file)

        # Get pandas.DataFrame table for the structure
        section_df = pd.DataFrame(structure_dict["sections"])
        section_df = section_df.set_index("id")
        question_df = pd.DataFrame(structure_dict["questions"])
        question_df = question_df.set_index("name")
        self.structure = {
            "sections": section_df,
            "questions": question_df,
        }

        # Update default plotting options
        self.cmap = cmap
        self.output_folder = output_folder
        self.figsize = figsize

    def read_responses(self, responses_file: str) -> None:
        """Read responses CSV file

        Args:
            responses_file (str): Path to the responses CSV file

        Raises:
            ValueError: The structure of the CSV file does not correspond to
              the structure in the XML file
        """
        # Read the CSV file
        # TODO: pd.read_csv

        # Validate the data:
        # * Compare the the structure with `self.structure`
        # * Something else?
        # TODO: ...

        # Process the data (optional for now)
        # * Optimize dtypes. At least for category fields
        # the dtype can be optimized using category.
        # * Clean values. Make sure that NA, None, etc. parsed properly
        # TODO: ...

        # Save to `self`
        # TODO: self.responses = responses

        raise NotImplementedError()

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

    @property
    def questions(self) -> pd.DataFrame:
        """Get information about the quesions

        Returns:
            pd.DataFrame: A data frame with information about the
              questions in the survey
        """
        raise NotImplementedError()

    @property
    def sections(self) -> pd.DataFrame:
        """Get information about the sections

        Returns:
            pd.DataFrame: A data frame with information about the
              sections in the survey, consisting of columns:
              section_id, section_title, section_info, question_count
        """
        raise NotImplementedError()
