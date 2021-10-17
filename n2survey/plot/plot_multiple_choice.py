from textwrap import wrap

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from n2survey import lime


def load_raw_data(path_to_data, question_id):
    """
    Loads raw data csv file into dataframe

    Args:
        path_to_data (str): Path to raw data csv file
        question_id (str): Code/id of the question to plot

    Returns:
        dataframe: A dataframe containing raw data for response to specified question
    """

    # Read csv into dataframe
    raw_data = pd.read_csv(path_to_data)

    # Select columns containing response to specified question
    columns = [
        column
        for column in raw_data.columns
        if column[: len(question_id) + 1] == question_id + "["
    ]

    return raw_data[columns]


def preprocess_data(data_df, display_threshold):
    """
    Preprocesses data

    Args:
        data_df (Dataframe): Dataframe containing response data
        display_threshold (float): Percentage threshold of the category to be included in the plot

    Returns:
        int: Total number of responses
        dataframe: A dataframe containing processed data
    """

    # Process data
    response_raw = data_df.notnull()

    # Create new 'Percentage' column
    response_counts = pd.DataFrame(response_raw.sum(axis=0))
    response_counts = response_counts.rename(columns={0: "counts"})
    total_response = response_raw.shape[0]
    response_counts["percentage"] = response_counts["counts"] / total_response * 100

    # Filter out categories below threshold
    response_to_plot = response_counts[
        response_counts["percentage"] >= display_threshold
    ].sort_values(by="percentage", ascending=False)

    return total_response, response_to_plot


def extract_question_info(path_to_structure, question_id):
    """
    Extracts texts for question and response options

    Args:
        path_to_structure (str): path to survey structure xml file
        question_id (str): Code/id of the question to plot

    Returns:
        dict: dictionary containing texts for question title and response categories
    """

    # Parse xml file into dictionary
    structure_dict = lime.read_lime_questionnaire_structure(path_to_structure)

    # Extract texts for specified question
    text_dict = {}
    for question in structure_dict["questions"]:
        if question["question_group"] == question_id:
            if question["name"][-5:] != "other":
                text_dict["question_text"] = question["label"]
                text_dict[question["name"].replace("_", "[") + "]"] = question[
                    "choices"
                ]["Y"]
                text_dict[question["name"].replace("T", "[other]")] = "Other"

    return text_dict


def create_bar_plot(
    data_df,
    text_dict,
    total_response,
    color_scheme,
    display_title,
    fig_dim,
    bar_thickness,
    bar_spacing,
    wrap_text,
):
    """
    Creates bar plot

    Args:
        data_df (dataframe): Dataframe containing data to be plotted
        text_dict (dict): Dictionary containing texts for question and response categories
        total_reponse (int): Total number of responses
        color_scheme (str): Color scheme of the plot
        display_title (bool): Whether to display the question title or not
        fig_dim (tuple of int): Dimensions of the plot. If none is given, default is (10, number of options * 2)
        display_no_answer (bool): Whether to display the "No answer" category or not
        wrap_text (bool): Whether to wrap text labels if they are too long for a single line
    """

    # Create tick labels
    tick_labels = [text_dict[column] for column in data_df.index]
    if wrap_text:
        tick_labels = ["\n".join(wrap(label, 20)) for label in tick_labels]

    # Create figure
    default_fontsize = 15
    bar_height = bar_thickness / (2 * bar_spacing)
    max_data = max(data_df["percentage"])
    min_data = min(data_df["percentage"])
    if fig_dim is None:
        fig_dim = (8, max(bar_spacing * data_df.shape[0] * 0.8, 8))
    fig = plt.figure(figsize=fig_dim)

    # Create bar plot
    ax = sns.barplot(
        x=data_df["percentage"], y=data_df.index, palette=color_scheme, orient="h"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xticks([])
    ax.set_yticklabels(tick_labels, fontsize=default_fontsize / bar_spacing - 5)
    plt.xlabel("")
    plt.xlim(max(0, min_data - 0), min(100, max_data + 0))

    # Create data annotation for each bar
    for bar in ax.patches:
        current_height = bar.get_height()
        bar.set_height(bar_height)
        bar_width = bar.get_width()
        bar.set_y(bar.get_y() + (current_height - bar_height) * 0.5)
        plt.annotate(
            f"{int(bar_width)}%",
            xy=(bar_width, bar.get_y() + bar.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            fontsize=default_fontsize / bar_spacing - 3,
            ha="left",
            va="center",
        )

    # Display texts
    wrapped_title = "\n".join(wrap(text_dict["question_text"], 45))
    wrapped_bottom = "\n".join(wrap(text_dict["question_text"], 55))
    if display_title:
        plt.text(
            x=-5, y=-1, s=wrapped_title, fontsize=default_fontsize * 1.2 / bar_spacing
        )
    bottom_text = (
        f"""Total: {total_response}\n\'{wrapped_bottom}\' Relative response rates """
    )
    plt.title(bottom_text, fontsize=default_fontsize * 0.9 / bar_spacing, y=-0.1)

    plt.subplots_adjust(left=0.25, right=0.9, top=0.8, bottom=0.1)

    plt.show()

    return fig


def plot_multiple_choice_question(
    path_to_data,
    question_id,
    path_to_structure=None,
    color_scheme="Blues_d",
    display_title=False,
    fig_dim=None,
    bar_thickness=1,
    bar_spacing=1,
    display_no_answer=False,
    display_threshold=0,
    wrap_text=True,
    save_fig_file=False,
):
    """
    Plots the response to a multiple choice question as a horizontal barplot

    Args:
        path_to_data (str): Path to raw data csv file
        question_id (str): Code/id of the question to plot
        path_to_structure (str): Path to survey structure xml file
        color_scheme (str): Color scheme of the plot
        display_title (bool): Whether to display the question title or not
        fig_dim (tuple of int): Dimensions of the plot. If none is given, default is (10, number of options * 2)
        display_no_answer (bool): Whether to display the "No answer" category or not
        display_threshold (float): Percentage threshold of the category to be included in the plot
        wrap_text (bool): Whether to wrap text labels if they are too long for a single line
        save_fig_file (bool): Whether to save the figure to png file
    """

    # Load raw data
    data_df = load_raw_data(path_to_data, question_id)

    # Preprocess data
    total_response, data_to_plot = preprocess_data(data_df, display_threshold)

    # Extract question and response texts
    if path_to_structure is not None:
        text_dict = extract_question_info(path_to_structure, question_id)

    # Create generic texts as substitute if real data unavailable
    else:
        text_dict = {
            question_id
            + "[SQ"
            + str(i).zfill(3)
            + "]": "Option "
            + str(i)
            + " text" * 10
            for i in range(1, len(data_df.shape[1]) + 5)
        }
        text_dict[question_id + "[other]"] = "Other"
        text_dict["question_text"] = f"Question {question_id} asks..."

    fig = create_bar_plot(
        data_to_plot,
        text_dict,
        total_response,
        color_scheme,
        display_title,
        fig_dim,
        bar_thickness,
        bar_spacing,
        wrap_text,
    )

    # Save figure to file
    if save_fig_file:
        fig.savefig(f"{question_id}_bar.png")
