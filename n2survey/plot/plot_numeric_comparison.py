from textwrap import wrap
from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

__all__ = ["comparison_numeric_bar_plot"]


def get_median_and_range(survey, question, responses):
    """Return the median (e.g. 550) and the corresponding range (e.g. 501-600)

    Median calculation and conversion to range works only when there is not averaging
    involved in median calculation, meaning that the number of array elements has to be
    uneven!
    If not, remove the largest element (making the array uneven) before calculation of
    the median. This reproduces the 'correct' result as long as the ranges of the two
    values in the middle of the array are of the same size!

    Even input: ... (501-600) (601-700) ... --> ... (550) (650) ...
    Median:                                 -->        (600)
    Range conversion:     (501-600)         <--

    Args:
        survey (LimeSurvey): LimeSurvey object
        question (str): investigated question, used for selecting data to calculate median.
        responses (DataFrame): unfiltered responses DataFrame

    Returns:
         median (float): Median of the filtered DataFrame
         range (str): Corresponding range needed for specifiying the x-plotting position
    """
    # question-codes for questions that were transformed from range --> numeric
    # median calculation only works for these and the transformation has to be done before
    transformed_questions = {
        "B1b": "noincome_duration",
        "B2": "income_amount",
        "B3": "costs_amount",
        "B4": "contract_duration",
        "B10": "holiday_amount",
        "C4": "hours_amount",
        "C8": "holidaytaken_amount",
    }
    if question in transformed_questions.keys():
        transformed_question = transformed_questions[question]
        transformed_answers = survey.get_responses(transformed_question)
        filtered_transformed_answers = transformed_answers.loc[responses.index]
        # check if at least one valid (non-NaN) value is there
        if np.sum(filtered_transformed_answers.count()) > 0:
            # calculate median depending on the number of non-NaN entries
            if np.sum(filtered_transformed_answers.count()) % 2:  # uneven
                median = np.nanmedian(filtered_transformed_answers)
            else:  # even
                # exclude the highest value to get uneven number of values
                # otherwise median = average of both middle values which
                # cannot be easily reversed back into a range
                index_max = filtered_transformed_answers.idxmax()
                median = np.nanmedian(filtered_transformed_answers.drop(index_max))
            # find corresponding range in original answers, used for plotting
            index, _ = np.where(transformed_answers == median)
            range = survey.get_responses(question).iloc[index[0]][0]
            return median, range
        else:
            return np.nan, np.nan
    else:
        return np.nan, np.nan


def comparison_numeric_bar_plot(
    survey,
    question,
    list_of_responses,
    list_of_data,
    list_of_labels: list = None,
    total: Union[int, float, None] = None,
    title: Optional[str] = None,
    fig_size_inches: tuple = None,
    display_percents: bool = False,
    display_total: bool = True,
    display_median: bool = True,
    display_no_answer: bool = True,
    wrap_text=True,
    percent_threshold=5,
    yaxis_max=None,
    theme: Optional[Dict] = None,
) -> Tuple[mpl.figure.Figure, mpl.axes.Axes]:
    """Do a multiple bar plots for a numeric single-choice question with multiple filters.

    Args:
        question (str): investigated question, used for selecting data to calculate median.
        list_of_responses (list): unfiltered and filtered data to plot.
        list_of_data (list): unfiltered and filtered counted data to plot.
        list_of_labels (list): labels for the entries in `list_of_data`.
        total (Union[int, float, None], optional): Total number to calculate percentage
          and to show on the figure. By default, sum of Y values is used.
        title (Optional[str], optional): Title of the axes. Defaults to None.
        display_percents (bool, optional): Show percents on top of boxes. Defaults to False.
        display_total (bool, optional): Show total number on the figure. Defaults to True.
        display_median (bool, optional): Show median of distribution. Defaults to True.
        display_no_answer (bool, optional): show 'No answer' possiblities. Defaults to True.
        wrap_text (bool, optional): Add line breaks to long questions. Defaults to True.
        percent_threshold (int, optional): Threshold for displaying percentages over bars.
        y_axis_max (): Maximum of y-axis, array-like or the same value for all if int.
        theme (Optional[Dict], optional): seaborn theme parameters.
          See `seaborn.set_theme` for the details. Defaults to None.

    Returns:
        tuple[mpl.figure.Figure, mpl.axes.Axes]: tuple (fig, ax) of the plot
    """
    # Additional parameters to provide in `sns.barplot`
    additional_params = {}

    # Elements of color `palette` are used for individual subplots
    palette = None
    if theme is not None:
        sns.set_theme(**theme)
        palette = theme.get("palette", None)
    else:
        palette = sns.color_palette()

    # Comparison only done in one figure (max. 9 subplots)
    if len(list_of_data) > 9:
        raise NotImplementedError(
            "Implementation only supports a maximum of 8 comparisons!"
        )

    # set figure size according to the number of subplots and x-axis entries
    if fig_size_inches is None:
        fig_size_inches = (len(list_of_data[0]) / 2.0, 2.0 * len(list_of_data))

    # filter out all 'No answer' entries for all dataframes
    if not display_no_answer:
        try:
            for i in range(len(list_of_data)):
                list_of_data[i] = list_of_data[i].drop("No Answer")
        except KeyError:
            pass

    # Prepare figure:
    # Total at top, all other filtered data below
    fig, ax = plt.subplots(len(list_of_data), 1, sharex=True)
    fig.set_size_inches(fig_size_inches)
    fig_width, _ = fig.get_size_inches()

    if yaxis_max is not None:
        if isinstance(yaxis_max, int):
            yaxis_max = np.ones(len(list_of_data)) * yaxis_max
        else:
            if len(np.asarray(yaxis_max)) == len(list_of_data):
                pass
    # Do the plots: unfiltered at top, then all plots with filtered data
    for i in range(len(list_of_data)):
        data = list_of_data[i]
        x = data.iloc[:, 0].index.values.tolist()
        y = data.iloc[:, 0]
        sns.barplot(x=x, y=y, ci=None, ax=ax[i], color=palette[i], **additional_params)
        ax[i].set(ylabel=None)
        total = np.array(y).sum()
        if display_total:
            ax[i].text(
                1.0,
                1.05,
                f"{list_of_labels[i]}: {total}",
                c=palette[i],
                horizontalalignment="right",
                verticalalignment="center",
                transform=ax[i].transAxes,
            )
        # Add percents on top
        if display_percents:
            percents = 100 * np.array(y) / total
            labels = [
                "{:.1f}%".format(p) if p > percent_threshold else "" for p in percents
            ]
            ax[i].bar_label(ax[i].containers[0], labels)
        # Add median as vertical dashed line
        if display_median:
            median, converted_range = get_median_and_range(
                survey, question, list_of_responses[i]
            )
            if converted_range in np.asarray(x):
                plot_position = np.where(np.asarray(x) == converted_range)[0]
                ax[i].axvline(x=plot_position, ls="--", c="grey")
                ax[i].text(
                    plot_position,
                    1.20 * np.max(y),
                f"{default_median}",
                c="white",
                weight="bold",
                path_effects=[pe.withStroke(linewidth=2, foreground="black")],
            )
        # Adjust yscale manually to show highest percentage values
        if yaxis_max is not None:
            ax[i].set_ylim(0, yaxis_max[i])
        else:
            ax[i].set_ylim(0, 1.40 * np.max(y))
        ax[i].yaxis.get_major_locator().set_params(integer=True)

    # Set y-label only for the axis (roughly) in the middle
    ax[int(len(list_of_data) / 2)].set_ylabel("Number of Responses")

    # Set title for uppermost axes
    if title is not None:
        wrapped_title = "\n".join(wrap(title, 55))
        ax[0].set_title(wrapped_title, pad=20)

    # Figure settings
    fig.tight_layout()
    fig.autofmt_xdate()
    fig.subplots_adjust(top=0.90, hspace=0.3)

    return fig, ax
