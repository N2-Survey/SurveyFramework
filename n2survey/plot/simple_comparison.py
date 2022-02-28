from typing import Union

import matplotlib.pyplot as plt
import numpy as np

__all__ = ["simple_comparison_plot"]


def get_percentages(array, totalbar=None):
    """
    This function calculates the total number of combinations from the given
    array of answer combinations.
    After that it adds the totalbar, if wanted, then it calculates a dictionary
    with the percentages for each combination+the totalbar if wanted
    """
    # get possible combinations (combi) and count how often they occure (no_of)
    (existing_combinations, occurences) = np.unique(
        array.astype(str), return_counts=True, axis=0
    )
    # if a totalbar array is calculated in the plot function survey.py
    # it will be appended to the beginning of combi and no_of
    if totalbar:
        total_combi = np.full((totalbar[0].shape[0], 1), "Total")
        total_combi = np.append(
            total_combi, np.reshape(totalbar[0], newshape=(-1, 1)), axis=1
        )
        existing_combinations = np.append(total_combi, existing_combinations, axis=0)
        occurences = np.append(totalbar[1], occurences)
    # Total values are converted to percentages and packed into a dictionary,
    # which is less confusing then pandas dataframe
    percentage = {}
    for answer in existing_combinations[:, 0]:
        answer_rows = np.where(existing_combinations[:, 0] == answer)
        percentage[answer] = np.append(
            np.reshape(existing_combinations[answer_rows, 1], newshape=(-1, 1)),
            np.reshape(
                np.round(
                    occurences[answer_rows] / sum(occurences[answer_rows]) * 100,
                    decimals=1,
                ),
                newshape=(-1, 1),
            ),
            axis=1,
        )
    return percentage


def form_x_and_y(df, totalbar=None, answer_suppress=False):
    """
    This function splits up the array given to it to x and y components for
    the plot.
    it collects the percentages of the people that answered the 'compare_with'
    question and the correlation with the answers those people gave to the
    main 'question'.
    It filters out the answers specified by answer_suppress.
    """
    percentages_for_comparison = []
    for entry in df:
        percentage_correlated_answers = get_percentages(entry, totalbar=totalbar)
        # totalbar only needs one appearence with the first entry in the df
        # which is the combinations of "question" and "compare_with"
        # the same totalbar is not calculated for additional questions in
        # 'add_questions' that are also compared with the compare_with_question
        # in 'plot'()-function of survey.py
        totalbar = None
        if answer_suppress:
            for answer in answer_suppress:
                if answer not in percentage_correlated_answers:
                    print(f"{answer} does not exist for this question")
                else:
                    percentage_correlated_answers.pop(answer)
        percentages_for_comparison.append(percentage_correlated_answers.copy())

    x = []
    y = []
    for percentage_correlated_answers in percentages_for_comparison:
        for entry in percentage_correlated_answers:
            x.append(entry)
            y.append(percentage_correlated_answers[entry])
    return x, y


def form_bar_positions(df, bar_positions=False, totalbar=None, answer_suppress=[]):
    """
    forms a complete list of bar positions for all bars, also the not
    specified ones.
    You can specify bar positions in a list, but if you
    want to specify the last bar you have to specify every bar before that,
    Maybe this can be improved for more user friendlieness.
    --> maybe exchange to a bar distance dictionary?
    if dictionary to complex for standard user, maybe list of tuples?
    [('Total',1.5),('Yes', 0.2),] etc.
    with (nameofbar, distance_from_previous_bar)
    At the moment we calculate PERCENTAGE a second time in this function,
    but the slowing of the whole plot function is neglectable.
    """
    # start list of bar_positions
    bar_positions_complete = bar_positions or [0]
    count = 0
    number_of_answers = 0
    for answer_combinations in df:
        percentage_correlated_answers = get_percentages(
            answer_combinations, totalbar=totalbar
        )
        for answer in answer_suppress:
            if answer not in percentage_correlated_answers:
                print(f"{answer} does not exist for this question")
            else:
                percentage_correlated_answers.pop(answer)
        number_of_answers = number_of_answers + len(percentage_correlated_answers)
        totalbar = None
        if count > 0 and len(bar_positions_complete) == number_of_answers - len(
            percentage_correlated_answers
        ):
            bar_positions_complete.append(max(bar_positions_complete) + 1.5)
        while len(bar_positions_complete) < number_of_answers:
            bar_positions_complete.append(max(bar_positions_complete) + 1)
        count = count + 1
    return bar_positions_complete


def filter_answer_sequence(x, answer_sequence):
    """
    removes answers from sequence that where supressed while creating x
    """
    all_answer_sequence = []
    for answer_list in answer_sequence:
        all_answer_list = answer_list.copy()
        for answer in answer_list:
            if answer not in x:
                all_answer_list.remove(answer)
        for answer in all_answer_list:
            all_answer_sequence.append(answer)
    return all_answer_sequence


def sort_data(sequence, x, y):
    """
    sorts lists x and y by comparing x and list sequence by rearranging x and y
    simoultaneously until x == sequence --> all entries in sequence have to
    also be in x
    at the moment each answer can only occure once in the plot, so if
    you want to add questions it is necessary to supress e.g. the 'no_answer'
    answer, else it would give an error. Can be improved in future.
    """
    indizes = []
    for x_entry in x:
        if np.where(np.array(sequence) == x_entry)[0].shape[0] == 1:
            position = sequence.index(x_entry)
            indizes.append(position)
        else:
            print(f"double bar: {x_entry}")
            raise NotImplementedError(
                """
                only single occurence of bars supported at the moment
                """
            )
    x_sorted = [entry for _, entry in sorted(zip(indizes, x))]
    y_sorted = [entry for _, entry in sorted(zip(indizes, y))]
    return x_sorted, y_sorted


def calculate_title_pad(labels, legend_columns, legend_title: Union[str, bool] = None):
    pad = int(len(labels) / legend_columns) * 20 + 20
    if legend_title:
        pad = pad + 20
    return pad


def simple_comparison_plot(
    plot_data_list,
    answer_suppress: list = [],
    no_answer_supress: bool = True,
    totalbar: np.ndarray = None,
    bar_positions: Union[list, bool] = False,
    threshold_percentage: float = 0,
    bar_width: float = 0.8,
    legend_columns: int = 2,
    plot_title: Union[str, bool] = False,
    plot_title_position: tuple = (()),
    legend_title: str = None,
    answer_sequence: list = [],
):
    """
    Plots correlations from the np.ndarray arrays in plot_data_list with the
    existing answer combinations and applies the given specifications.
    """
    # form x-axis with answers to first question and y-axis with
    # percentages of second question correlated to each answer of the first
    # question.
    if no_answer_supress:
        answer_suppress.append("No Answer")
    (x, y) = form_x_and_y(
        plot_data_list, totalbar=totalbar, answer_suppress=answer_suppress
    )
    # complete and filter answer sequence after sorting out answers
    answer_sequence = filter_answer_sequence(x, answer_sequence)
    # create a list with positonings of the bars in the plot.
    bar_positions_complete = form_bar_positions(
        plot_data_list,
        bar_positions,
        totalbar=totalbar,
        answer_suppress=answer_suppress,
    )
    # sort x and y to follow answer_sequence
    (x, y) = sort_data(answer_sequence, x, y)
    # %% Prepare/Define figure
    fig, ax = plt.subplots()
    # %% split up y to list of answers of question 2 and list of percentages
    q2_answers = []
    percentages = []
    for entry in y:
        q2_answers.append(entry[:, 0])
        percentages.append(entry[:, 1].astype(np.float64))
    all_answers = np.unique(np.concatenate(np.array(q2_answers, dtype=object)))
    percentage_all = []
    for (percentage, q2_answer) in zip(percentages, q2_answers):
        count = 0
        percentage_all_single = []
        for answer in all_answers:
            if answer in q2_answer:
                percentage_all_single.append(percentage[count])
                count = count + 1
            else:
                percentage_all_single.append(0)
        percentage_all.append(percentage_all_single.copy())
    # %% plot and format
    bottom = 0
    count = 0
    for answer, percentage in zip(all_answers, np.transpose(np.array(percentage_all))):
        ax.bar(
            bar_positions_complete,
            percentage,
            bottom=bottom,
            label=answer,
            width=bar_width,
        )
        plt.xticks(bar_positions_complete, x)
        bottom = bottom + percentage
        labels = percentage.astype(str)
        labels[np.where(labels.astype(np.float64) <= threshold_percentage)] = ""
        ax.bar_label(ax.containers[count], labels, fmt="%s", label_type="center")
        count = count + 1
    labels = all_answers
    ax.legend(
        labels,
        bbox_to_anchor=([0.1, 1, 0, 0]),
        ncol=legend_columns,
        frameon=False,
        title=legend_title,
    )
    ax.axes.get_yaxis().set_visible(False)
    if plot_title:
        if plot_title_position:
            ax.text(plot_title_position[0], plot_title_position[1], plot_title)
        else:
            ax.set_title(
                plot_title,
                pad=calculate_title_pad(
                    labels, legend_columns, legend_title=legend_title
                ),
            )
    # scale
    plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment="right")
    # figure settings
    fig.tight_layout()
    return fig, ax
