from textwrap import wrap

import matplotlib.pyplot as plt
import seaborn as sns

__all__ = ["multiple_choice_bar_plot"]


def create_bar_plot(
    data_df,
    tick_labels,
    palette,
    display_title,
    fig_dim,
    bar_thickness,
    bar_spacing,
):
    """
    Create bar plot

    Args:
        data_df (dataframe): Dataframe containing data to be plotted
        tick_labels (list): list of tick labels
        color_scheme (str): Color scheme of the plot
        display_title (bool): Whether to display the question title or not
        fig_dim (tuple of int): Dimensions of the plot. If int, it will be (fig_dim, fig_dim). If none is given, default is (10, number of options * 2)
        display_no_answer (bool): Whether to display the "No answer" category or not
        wrap_text (bool): Whether to wrap text labels if they are too long for a single line
    """

    # Set up parameters
    default_fontsize = 15
    bar_height = bar_thickness / (2 * bar_spacing)
    max_data = max(data_df.iloc[:, 0])
    total = get_total(data_df)
    is_percentage = data_df.dtypes[0] == "float64"

    # Create figure
    if fig_dim is None:
        fig_dim = (8, max(bar_spacing * data_df.shape[0] * 0.8, 8))
    fig = plt.figure(figsize=fig_dim)

    # Create bar plot
    ax = sns.barplot(x=data_df.iloc[:, 0], y=data_df.index, palette=palette, orient="h")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.set_xticks([])
    ax.set_yticklabels(tick_labels, fontsize=default_fontsize / bar_spacing - 5)
    plt.xlabel("")
    plt.ylabel("")
    plt.xlim(0, max_data)

    # Create data annotation for each bar
    for bar in ax.patches:
        current_height = bar.get_height()
        bar.set_height(bar_height)
        bar_width = bar.get_width()
        bar.set_y(bar.get_y() + (current_height - bar_height) * 0.5)
        plt.annotate(
            f"{int(bar_width)}%" if is_percentage else f"{int(bar_width)}",
            xy=(bar_width, bar.get_y() + bar.get_height() / 2),
            xytext=(3, 0),
            textcoords="offset points",
            fontsize=default_fontsize / bar_spacing - 3,
            ha="left",
            va="center",
        )

    # Display texts
    wrapped_title = "\n".join(wrap(data_df.columns[0], 45))
    wrapped_bottom = "\n".join(wrap(data_df.columns[0], 55))
    if display_title:
        plt.text(
            x=0.5, y=-1, s=wrapped_title, fontsize=default_fontsize * 1.2 / bar_spacing
        )
    bottom_text = f"Total: {total}\n'{wrapped_bottom}'"
    if is_percentage:
        bottom_text = bottom_text + " Relative response rates."
    plt.title(bottom_text, fontsize=default_fontsize * 0.9 / bar_spacing, y=-0.1)

    # Adjust margins
    plt.subplots_adjust(left=0.25, right=0.9, top=0.8, bottom=0.1)

    return fig, ax


def get_total(data_df):
    """Get total number of responses

    Args:
        data_df (df): Dataframe of data to plot

    Returns:
        str: Total number, or 'Unknown' if cannot be determined.
    """

    if "Total" in data_df.columns:
        total = str(data_df.iloc[0].loc["Total"])
    else:
        total = "Unknown"

    return total


def make_tick_labels(data_df, wrap_text=True):
    """
    Create tick labels

    Args:
        data_df (df): Dataframe of data to plot
        question_chocies (dict): Dict mapping for answer choices
        wrap_text (bool): Whether to wrap text labels if they are too long for a single line

    Returns:
        list: list of tick labels
    """

    tick_labels = list(data_df.index)
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

    return data_df[data_df.iloc[:, 0] > display_threshold]


def sort_data(data_df, sort):
    """Sort data in ascending or descending order

    Args:
        data_df (df): Dataframe of data to plot
        sort (str): 'ascending' or 'descending' order to sort in

    Returns:
        df: Dataframe with data sorted in the specified order
    """

    if sort == "ascending":
        data_df = data_df.sort_values(data_df.columns[0], ascending=True)
    elif sort == "descending":
        data_df = data_df.sort_values(data_df.columns[0], ascending=False)

    return data_df


def multiple_choice_bar_plot(
    data_df,
    theme=None,
    # sort=None,
    sort="descending",
    # display_title=False,
    display_title=True,
    bar_thickness=1,
    # bar_spacing=1,
    bar_spacing=1.2,
    display_threshold=0,
    wrap_text=True,
):
    """
    Plot the response to a multiple choice question as a horizontal barplot

    Args:
        data_df (df): dataframe of counts and percentages
        sort (str, optional): 'ascending' or 'descending' order to sort in. If value other than these two, the df remains unchanged. Default is None.
        display_title (bool, optional): Whether to display the question title or not
        display_threshold (float, optional): Threshold of the category to be included in the plot. Can be either count or percentage.
        wrap_text (bool, optional): Whether to wrap text labels if they are too long for a single line
    """
    palette = None
    fig_dim = None
    if theme is not None:
        sns.set_theme(**theme)
        palette = theme.get("palette", "Blues_d")
        fig_dim = theme.get("rc", None).get("figure.figsize", None)

    filtered_data_df = filter_categories_below_threshold(data_df, display_threshold)

    if sort is not None:
        filtered_data_df = sort_data(filtered_data_df, sort)

    tick_labels = make_tick_labels(filtered_data_df, wrap_text)

    fig, ax = create_bar_plot(
        filtered_data_df,
        tick_labels,
        palette,
        display_title,
        fig_dim,
        bar_thickness,
        bar_spacing,
    )

    return fig, ax
