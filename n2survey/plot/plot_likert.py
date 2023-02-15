import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from .common import label_wrap

__all__ = ["likert_bar_plot"]

DEFAULT_GROUPED_CHOICES = [
    {
        "left": ["Yes"],
        "center": ["I don’t know", "I don’t want to answer this question", "No Answer"],
        "right": ["No"],
    },
    {
        "left": ["Very satisfied", "Satisfied"],
        "center": [
            "Neither/nor",
            "Does not apply",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "right": ["Dissatisfied", "Very dissatisfied"],
    },
    {
        "left": ["Very attractive", "Attractive"],
        "center": ["Neutral", "I don’t want to answer this question", "No Answer"],
        "right": ["Unattractive", "Very unattractive"],
    },
    {
        "left": ["Very much", "To some extent"],
        "center": [
            "Does not apply",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "right": [
            "Rather not",
            "Not at all",
        ],
    },
    {
        "left": ["Very much", "Moderately"],
        "center": ["I don’t want to answer this question", "No Answer"],
        "right": ["Somewhat", "Not at all"],
    },
    {
        "left": ["Not at all"],
        "center": ["I don’t want to answer this question", "No Answer"],
        "right": ["Several days", "More than half the days", "Nearly every day"],
    },
    {
        "left": ["Male"],
        "center": [
            "Diverse",
            "I don’t know",
            "Does not apply",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "right": ["Female"],
    },
    {
        "left": ["Fully agree", "Partially agree"],
        "center": [
            "Neither agree nor disagree",
            "I don’t know",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "right": ["Partially disagree", "Fully disagree"],
    },
    {
        "left": ["Very much", "Rather yes"],
        "center": [
            "Indifferent",
            "I don’t know",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "right": ["Rather not", "Not at all"],
    },
    {
        "left": ["Yes, to a great extent", "Yes, to some extent"],
        "center": ["I don’t know", "I don’t want to answer this question", "No Answer"],
        "right": ["No"],
    },
    {
        "left": ["very positively", "positively"],
        "center": [
            "neutral",
            "no base for comparison in my case",
            "I don’t know",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "right": ["negatively", "very negatively"],
    },
    {
        "left": ["never", "rarely"],
        "center": [
            "sometimes",
            "I don’t want to answer this question",
            "Does not apply",
            "No Answer",
        ],
        "right": ["often", "always"],
    },
    {
        "left": ["not at all", "rather not"],
        "center": [
            "I never had the option",
            "I don’t know",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "right": ["to some extent", "very much"],
    },
]


def get_grouped_default_choices(responses):
    """
    Get a dict of presorted choices (potential responses)
    Args:
        responses (list): responses given in the data

    Returns:
        dict: dict of sorted choices

    """
    for choices in DEFAULT_GROUPED_CHOICES:
        responses_lower = [response.lower() for response in responses]
        choices_lower = [choice.lower() for choice in choices_to_list(choices.values())]
        if len(set(responses_lower).difference(set(choices_lower))) == 0:
            return remove_unused_default_choices(responses, choices)

    raise AssertionError(
        f"No sorted default choices found for responses {responses} - "
        f"please provide your own sorting as follows: {DEFAULT_GROUPED_CHOICES[0]}"
    )


def remove_unused_default_choices(responses, choices):
    """
    Filter out default choices that are not occurring in the responses
    Args:
        responses (list): responses given in the data
        choices (dict): sorted choices (potential responses)

    Returns:
        dict: of sorted choices with choices that are not available in the responses removed

    """
    filtered_choices = dict()
    responses_lower = [response.lower() for response in responses]
    for location, groupded_choices in choices.items():
        filtered_choices[location] = [
            choice for choice in groupded_choices if choice.lower() in responses_lower
        ]

    return filtered_choices


def choices_to_list(choices):
    return [choice for grouped_choices in choices for choice in grouped_choices]


def clean_up_apostrophes_in_responses(data_df):
    """
    Replace apostrophes in the responses
    Args:
        data_df (df): Dataframe of data to plot

    Returns:
        df: Dataframe of data to plot

    """
    for response in data_df.index:
        if isinstance(response, str):
            data_df = data_df.rename(index={response: response.replace("'", "’")})
    return data_df


def get_colors(palette, grouped_choices):
    """
    Get colors for plotting
    Args:
        palette (str): if None a default palette is used otherwise a
        grouped_choices (dict): choices sorted by location where they will be plotted ("left", "center", "right")

    Returns:
        dict: for each plot location ("left", "center", "right") a list of colors

    """
    if palette is None:
        color_palette = {"left": "Blues", "center": "Greys", "right": "Reds"}
        colors = {
            position: sns.color_palette(color_map, len(grouped_choices[position]))
            for position, color_map in color_palette.items()
        }
        colors["left"] = colors["left"][
            ::-1
        ]  # flip color scale so dark colors on the out sides of the bars
    else:
        n_colors = sum([len(choices) for choices in grouped_choices.values()])
        color_palette = sns.color_palette(palette, n_colors=n_colors)
        colors = {
            "left": color_palette[: len(grouped_choices["left"])],
            "center": color_palette[
                len(grouped_choices["left"]) : -len(grouped_choices["right"])
            ],
            "right": color_palette[-len(grouped_choices["right"]) :],
        }
    return colors


def calc_y_bar_position(grouped_questions, bar_width, bar_spacing, group_spacing):
    """
    Calculate y axis position of bar plots

    Args:
        grouped_questions (list): each sub-list is a group of questions which will be plotted together
        bar_width (float): thickness of a single bar
        bar_spacing (float): horizontal spacing between bars belonging to the same group
        group_spacing (float): horizontal spacing between different question groups

    Returns:
        list: bar locations for plotting
    """
    bar_positions = []
    prev_position = 0
    for i_group, question_group in enumerate(grouped_questions):
        group_positions = (bar_width + bar_spacing) * np.array(
            (range(len(question_group)))
        ) + prev_position
        if i_group > 0:
            group_positions = group_positions + group_spacing
        bar_positions.extend(group_positions)
        prev_position = bar_positions[-1]
    return bar_positions


def format_labels(labels):
    """
    Format labels to be first letter upper case, all other characters lowercase.
    Args:
        labels (list): labels to be formatted

    Returns:
        list: formatted labels

    """
    edited_labels = []
    for label in labels:
        label = label.lower()
        label = label[0].upper() + label[1:]
        label = label.replace(" i ", " I ")
        edited_labels.append(label)
    return edited_labels


def sort_questions(data_df, grouped_questions, grouped_choices, sort_by_choices):
    """
    Sort questions in the dataframe to plot them in their group and sort them in their group according to the responses.
    Args:
        data_df (df): Dataframe of data to plot
        grouped_questions (list): each sub-list is a group of questions which will be plotted together
        grouped_choices (dict): choices sorted by location where they will be plotted ("left", "center", "right")
        sort_by_choices (str): choices by which to sort the questions ("left", "right", "no_sorting")

    Returns:
        df: Dataframe with reordered columns (columns represent the questions)
    """
    if sort_by_choices == "no_sorting":
        return data_df
    # sort questions by the selected sorting (left / right)
    # and add half of the "centered" responses as well since they shift the bars outside as well
    sorted_questions = (
        (
            data_df.loc[grouped_choices[sort_by_choices]].sum(axis=0)
            + data_df.loc[grouped_choices["center"]].sum(axis=0) / 2
        )
        .sort_values(ascending=False)
        .index
    )
    # resort data frame according to the groups so the questions are sorted within each group by the selected sorting
    sorted_group_questions = [
        question
        for question_group in grouped_questions
        for question in sorted_questions
        if question in question_group
    ]
    return data_df.reindex(columns=sorted_group_questions)


def absolute_responses_to_percentage(data_df):
    total_responses = data_df.sum(axis=0)
    data_df = data_df / total_responses * 100
    return data_df.round(1)


def check_question_sorting(sort_questions_by):
    available_sortings = ["left", "right", "no_sorting"]
    if sort_questions_by not in available_sortings:
        raise AssertionError(
            f"Unknown sorting of responses received {sort_questions_by}, allowed options: {available_sortings}"
        )


def likert_bar_plot(
    data_df,
    grouped_choices=None,
    grouped_questions=None,
    sort_questions_by_choices="left",
    plot_title=False,
    plot_title_position: tuple = (()),
    theme=None,
    bar_width=0.2,
    bar_spacing=0.5,
    group_spacing=1,
    legend_columns=2,
    calc_fig_size=True,
    x_axis_max_values=None,
    textwrap_y_axis: int = 100,
    max_textwrap_y_axis: int = 200,
    textwrap_legend: int = 100,
    max_textwrap_legend: int = 200,
    **kwargs,
):
    """
    Plot the responses to an array question as a Likert plot
    Args:
        data_df (df): dataframe of containing response counts (rows) and questions (columns)
        grouped_choices (dict, optional): choices sorted by location where they will be plotted ("left", "center", "right"). If None provided, a set of default pre-sorted choices is selected.
        grouped_questions (list, optional): each sub-list is a group of questions which will be plotted together. If None provided all columns are assigned to a single group.
        sort_by_choices (str, optional): choices by which to sort the questions ("left", "right", "no_sorting").
        plot_title (Union[str, bool], optional): Title of the plot.
        theme(dict, optional): plot theme. If None is provided a default theme is selected.
        bar_width (float): thickness of a single bar
        bar_spacing (float): horizontal spacing between bars belonging to the same group
        group_spacing (float): horizontal spacing between different question groups
        calc_fig_size (bool, optional): Calculate a figure size from the provided data and bar parameters, if False a default figure size is used
        x_axis_max_values (float, optional): Crop the x-Axis to [N%...N%], if None provided the x-axis is  [100%...100%]
    """
    palette = None

    check_question_sorting(sort_questions_by_choices)

    # total_answers = data_df.loc["Total", "Total"]
    data_df = data_df.drop("Total", axis=0)
    data_df = data_df.drop("Total", axis=1)

    data_df.index = data_df.index.map(str)
    data_df = clean_up_apostrophes_in_responses(data_df)

    if grouped_questions is None:
        grouped_questions = [data_df.columns.values]

    if grouped_choices is None:
        grouped_choices = get_grouped_default_choices(data_df.index)

    if calc_fig_size:
        if theme is not None:
            theme["rc"]["figure.figsize"] = (
                12,
                len(data_df.columns) * (bar_width + bar_spacing)
                + len(grouped_questions) * group_spacing
                + 0.5,
            )
        else:
            sns.set(
                rc={
                    "figure.figsize": (
                        12,
                        len(data_df.columns) * (bar_width + bar_spacing)
                        + len(grouped_questions) * group_spacing
                        + 0.5,
                    )
                }
            )

    if theme is not None:
        sns.set_theme(**theme)
        palette = theme.get("palette", None)

    fig, ax = plt.subplots()

    # rearrange responses in dataframe according to the selected sorting so they are plotted in the correct order
    location_and_response = [
        (position, choice)
        for position in ["left", "center", "right"]
        for choice in grouped_choices[position]
    ]

    _, sorted_responses = list(zip(*location_and_response))
    data_df = data_df.reindex(sorted_responses)

    # reorder dataframe columns and the questions for plotting according to the sorting
    n_responses_absolute = data_df.sum(axis=0)
    data_df = absolute_responses_to_percentage(data_df)
    data_df = sort_questions(
        data_df, grouped_questions, grouped_choices, sort_questions_by_choices
    )

    responses_cumulated = data_df.cumsum(axis=0)

    # dict of colors for the bar parts ["left", "center", "right"]
    colors = get_colors(palette, grouped_choices)

    bar_positions = calc_y_bar_position(
        grouped_questions, bar_width, bar_spacing, group_spacing
    )
    # own size + half of the size of the central box
    # have it centered around the choices assigned to the "center" location
    bar_offsets = (
        data_df.loc[grouped_choices["left"]].sum(axis=0)
        + data_df.loc[grouped_choices["center"]].sum(axis=0) / 2
    )

    sorted_questions = data_df.columns.values
    for response in location_and_response:
        position, response_name = response
        index_response = grouped_choices[position].index(response_name)
        widths = data_df.loc[response_name].values
        starts = responses_cumulated.loc[response_name].values - widths - bar_offsets
        ax.barh(
            bar_positions,
            widths,
            left=starts,
            height=bar_width,
            label=format_labels([response_name])[0],
            color=colors[position][index_response],
        )
        plt.yticks(
            bar_positions,
            label_wrap(data_df.columns.values, textwrap_y_axis, max_textwrap_y_axis),
        )

    # add counts per question
    for question, bar_position in zip(sorted_questions, bar_positions):
        n_counts = "Total:\n(" + str(int(n_responses_absolute[question])) + ")"
        ax.text(-10, bar_position + bar_width * 0.25, n_counts, color="black")

    # add zero reference line
    ax.axvline(0, linestyle="--", label=None, color="black", alpha=0.25)

    # x axis in percent
    if x_axis_max_values is not None:
        ax_min_max = x_axis_max_values
    else:
        ax_min_max = 100
    ax.set_xlim(-ax_min_max, ax_min_max)
    ax.set_xticks(np.arange(-ax_min_max, ax_min_max + 1, 20))
    ax.xaxis.set_major_formatter(lambda x, pos: str(abs(int(x))) + "%")

    # add total answers and answers per question
    # ax.text(ax_min_max, -0.05, f"Total: {total_answers}",size= mpl.rcParams["font.size"])

    # y axis
    ax.invert_yaxis()

    # remove spines
    ax.spines["right"].set_visible(False)
    ax.spines["top"].set_visible(False)
    ax.spines["left"].set_visible(False)

    # legend
    hax, lax = ax.get_legend_handles_labels()
    lax = label_wrap(lax, textwrap_legend, max_textwrap_legend)
    ax.legend(
        hax,
        lax,
        ncol=legend_columns,
        bbox_to_anchor=kwargs.get("bbox_to_anchor", [0.5, 1.1]),
        # mode="expand",
        frameon=False,
        loc="upper center",
        # framealpha=0.5,
    )

    # set plot title - already handled by outer plot function
    if plot_title:
        if plot_title_position:
            ax.text(plot_title_position[0], plot_title_position[1], plot_title)
        else:
            ax.set_title(plot_title, y=1.28)

    plt.tight_layout()
    return fig, ax
