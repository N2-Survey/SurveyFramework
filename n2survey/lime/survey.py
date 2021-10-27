import os
from typing import Optional, Tuple
import pandas as pd

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
        "default_plot_kinds": {
            "multiple choice": "multiple choice plot",
            "choice field": "basic bar plot",
            "rate": "likert scale plot"}
    }

    plot_kinds_ = [
        "multiple choice plot",
        "likert scale plot",
        "simple comparison plot",
        "basic bar plot"
    ]

    question_types = [
        "multiple choice",
        "choice field",
        "rate"
    ]

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

        Raises:
            NotImplementedError: [description]
        """
        # Parse XML structure file
        # TODO: ...

        # Get pandas.DataFrame table for the structure
        # TODO: self.structure = ...

        # Update default plotting options
        # TODO: ...

        raise NotImplementedError()

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
            if kind not in self.available_plot_types:
                raise TypeError("The chosen plot kind must be element of the"
                                "available plot types")
            # Check is the chosen plot kind is available
            # for the chosen question
            # TODO: ...

        plot_options = self.default_plot_options
        # Currently it is not checked if the given keyword has the rigth type
        # TODO: set default keyword arguments in the plot function?
        if kwargs:
            if not all([plot_option in self.default_plot_options for
                        plot_option in kwargs]):
                raise TypeError("The given keyword is not an available "
                                "plot option")

        # Call the corresponding plot function with the given plot_options
        if kind == "multple choice plot":
            raise NotImplementedError()

        if kind == "mikert scale plot":
            raise NotImplementedError()

        if kind == "simple comparison plot":
            raise NotImplementedError()

        if kind == "basic bar plot":
            raise NotImplementedError()

    def get_label(self, question: str) -> str:
        """Get label for the corresponding column or group of colums"""
        raise NotImplementedError()

    def get_choices(self, question: str) -> str:
        """Get choices for the corresponding column or group of colums"""
        raise NotImplementedError()

    @property
    def questions(self) -> pd.DataFrame:
        """Get information about the questions

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
