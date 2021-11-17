from textwrap import wrap

import matplotlib.pyplot as plt
import seaborn as sns


def create_bar_plot(
    data_df,
    question_label,
    tick_labels,
    color_scheme,
    display_title,
    fig_dim,
    bar_thickness,
    bar_spacing,
):
    """
    Create bar plot

    Args:
        data_df (dataframe): Dataframe containing data to be plotted
        question_label (str): Text label of the question to plot
        color_scheme (str): Color scheme of the plot
        display_title (bool): Whether to display the question title or not
        fig_dim (tuple of int): Dimensions of the plot. If none is given, default is (10, number of options * 2)
        display_no_answer (bool): Whether to display the "No answer" category or not
        wrap_text (bool): Whether to wrap text labels if they are too long for a single line
    """

    # Create figure
    default_fontsize = 15
    bar_height = bar_thickness / (2 * bar_spacing)
    max_data = max(data_df["percentage"])
    min_data = min(data_df["percentage"])
    total = data_df["counts"].sum()
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
    wrapped_title = "\n".join(wrap(question_label, 45))
    wrapped_bottom = "\n".join(wrap(question_label, 55))
    if display_title:
        plt.text(
            x=0.5, y=-1, s=wrapped_title, fontsize=default_fontsize * 1.2 / bar_spacing
        )
    bottom_text = f"""Total: {total}\n\'{wrapped_bottom}\' Relative response rates """
    plt.title(bottom_text, fontsize=default_fontsize * 0.9 / bar_spacing, y=-0.1)

    plt.subplots_adjust(left=0.25, right=0.9, top=0.8, bottom=0.1)

    plt.show()

    return fig


def make_tick_labels(data_df, question_choices, wrap_text=True):
    """
    Create tick labels

    Args:
        data_df (df): Dataframe of data to plot
        question_chocies (dict): Dict mapping for answer choices
        wrap_text (bool): Whether to wrap text labels if they are too long for a single line

    Returns:
        list: list of tick labels
    """

    tick_labels = [question_choices[column] for column in data_df.index]
    if wrap_text:
        tick_labels = ["\n".join(wrap(label, 20)) for label in tick_labels]

    return tick_labels


def filter_categories_below_threshold(data_df, display_threshold):
    """Filter categories below threshold from dataframe

    Args:
        data_df (df): Dataframe of data to plot
        display_threshold (float): Percentage threshold of the category to be included in the plot

    Returns:
        df: Dataframe with categories above display threshold only
    """

    return data_df[data_df["percentage"] > display_threshold]


def make_bar_plot_for_multiple_choice_question(
    data_df,
    question_label,
    question_choices,
    color_scheme="Blues_d",
    display_title=False,
    fig_dim=None,
    bar_thickness=1,
    bar_spacing=1,
    display_threshold=0,
    wrap_text=True,
    save_fig_file=False,
):
    """
    Plot the response to a multiple choice question as a horizontal barplot

    Args:
        data_df (df): dataframe of counts and percentages
        question_label (str): Text label of the question to plot
        question_choices (dict): dict mapping for answer chocies
        color_scheme (str): Color scheme of the plot
        display_title (bool): Whether to display the question title or not
        fig_dim (tuple of int): Dimensions of the plot. If none is given, default is (10, number of options * 2)
        display_threshold (float): Percentage threshold of the category to be included in the plot
        wrap_text (bool): Whether to wrap text labels if they are too long for a single line
        save_fig_file (bool): Whether to save the figure to png file
    """

    filtered_data_df = filter_categories_below_threshold(data_df, display_threshold)

    tick_labels = make_tick_labels(filtered_data_df, question_choices, wrap_text)

    fig = create_bar_plot(
        filtered_data_df,
        question_label,
        tick_labels,
        color_scheme,
        display_title,
        fig_dim,
        bar_thickness,
        bar_spacing,
    )

    # Save figure to file
    if save_fig_file:
        fig.savefig("multiple_choice_bar.png")
