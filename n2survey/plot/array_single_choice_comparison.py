#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 09:38:31 2022

@author: theflike
"""

from textwrap import wrap
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from .comparison_shared_functions import (
    aspect_ratio_from_arguments,
    calculate_title_pad,
    form_bar_positions,
    form_single_answer_bar_positions,
)
from .plot_likert import DEFAULT_GROUPED_CHOICES


def array_single_comparison_plot(
    plot_data_list,
    suppress_answers: list = [],
    ignore_no_answer: bool = True,
    totalbar: np.ndarray = None,
    bar_positions: list = [],
    threshold_percentage: float = 0,
    bar_width: float = 0.8,
    legend_columns: int = 2,
    plot_title: Union[str, bool] = False,
    plot_title_position: tuple = (()),
    legend_title: str = None,
    answer_sequence: list = [],
    legend_sequence: list = [],
    theme=None,
    calculate_aspect_ratio: bool = True,
    maximum_length_x_axis_answers=20,
    show_zeroes: bool = True,
    bubbles: Union[bool, float] = None,
    no_sub_bars: bool = False,
    combine_neutral_choices: bool = True,
):

    """
    Plots correlations between array answers and the answers of
    single choice questions.
    """

    # for answer in compare_with_answers:
    y_labels = [entry for entry in plot_data_list[0][0][0]]
    grouped_choices = get_grouped_choices(
        options=plot_data_list[0][0][1], all_grouped_choices=DEFAULT_GROUPED_CHOICES
    )
    answer_dictionary, choices = get_answer_dictionary(
        array_question_data=plot_data_list[0][0],
        compare_with_data=plot_data_list[0][1],
        legend_sequence=legend_sequence,
        grouped_choices=grouped_choices,
        totalbar=totalbar,
    )
    # remove answers from compare_with answers dictionary
    for answer in answer_dictionary.copy():
        if not answer_dictionary[answer]:
            answer_dictionary.pop(answer, None)
            legend_sequence.remove(answer)
        elif answer in suppress_answers:
            answer_dictionary.pop(answer, None)
            legend_sequence.remove(answer)
        else:
            pass
    positionlist_per_answer = form_single_answer_bar_positions(
        answer_dictionary,
        bar_width,
        bar_positions_per_answer=bar_positions,
        multiplicator=1,
    )
    y = answer_sequence
    bar_positions_complete = form_bar_positions(
        y,
        answer_dictionary,
        bar_width=bar_width,
        totalbar=totalbar,
        distance_between_bars=2,
        positionlist_per_answer=list(positionlist_per_answer),
        no_sub_bars=no_sub_bars,
        multiplicator=1,
    )
    # %%% calculate dimensions of figure
    if theme is not None:
        if calculate_aspect_ratio:
            height, width = aspect_ratio_from_arguments(
                bar_positions_complete,
                positionlist_per_answer,
                theme,
                bar_width,
                max_lines_xtick=3,
                max_lines_ytick=3,
                multiplicator=0.4,
            )
            width = theme["rc"]["figure.figsize"][0]
        else:
            width, height = theme["rc"]["figure.figsize"]
        theme["rc"]["figure.figsize"] = (width, height)
        sns.set_theme(**theme)

    # initialize Figure
    fig, ax = plt.subplots()
    fig.set_tight_layout(True)
    colormap = plt.get_cmap(theme["palette"])
    ax.set_prop_cycle(
        color=[
            colormap(1.0 * i / len(legend_sequence))
            for i in range(len(legend_sequence))
        ]
    )
    colors = [
        colormap(1.0 * i / len(legend_sequence)) for i in range(len(legend_sequence))
    ]

    # plot
    answer_count = 0
    for answer, sub_position in zip(legend_sequence, positionlist_per_answer):
        count = 0
        percentage_groups = np.array(answer_dictionary[answer])
        bar_positions = bar_positions_complete + sub_position
        for column, choice in zip(np.transpose(percentage_groups), choices):
            starts = calculate_bar_starts_from_data(
                column, choice, grouped_choices, percentage_groups, count
            )
            if choice in grouped_choices["left"]:
                width = -column
            else:
                width = column
            ax.barh(
                bar_positions,
                width=width,
                left=starts,
                height=bar_width,
                label=answer,
                align="edge",
                edgecolor="black",
                color=colors[answer_count],
            )
            count = count + 1
        answer_count = answer_count + 1
    plt.legend(
        legend_sequence,
        loc=(0.1, 1),
        ncol=legend_columns,
        frameon=False,
        title=legend_title,
    )
    legend = ax.get_legend()
    count = 0
    for color in colors:
        legend.legendHandles[count].set_color(color)
        count = count + 1

    labels = grouped_choices["left"]
    labels.append("all neutral choices")
    labels = labels + grouped_choices["right"]
    separator = " "
    while len(separator) <= 2 * (theme["rc"]["figure.figsize"][0] / len(labels)):
        separator = separator + " "
    labels = separator.join(labels)
    plt.xlabel(
        labels,
    )
    plt.xlim(-100, 100)
    if plot_title:
        if plot_title_position:
            ax.text(plot_title_position[0], plot_title_position[1], plot_title)
        else:
            ax.set_title(
                plot_title,
                pad=calculate_title_pad(
                    legend_sequence,
                    legend_columns,
                    theme=theme,
                    legend_title=legend_title,
                ),
            )
    ax.invert_xaxis()

    # wrap text in x-axis and, if bubbles, y-axis texts as well
    y_labels = [
        "\n".join(wrap(entry, width=maximum_length_x_axis_answers))
        for entry in y_labels
    ]
    plt.yticks(bar_positions_complete, y_labels)
    plt.setp(ax.get_yticklabels(), rotation=30, horizontalalignment="right")

    return fig, ax


def get_grouped_choices(options, all_grouped_choices):
    """
    returns the dictionary that contains all options of the 'question'
    from the list of dictionaries contanining all options of every question
    """
    count = 0
    for entry in all_grouped_choices:
        entry_list = [entry[x] for x in entry]
        for option in options:
            if any(option in x for x in entry_list):
                index = count
            else:
                break
        count = count + 1
    return all_grouped_choices[index]


def get_answer_dictionary(
    array_question_data,
    compare_with_data,
    legend_sequence,
    grouped_choices,
    combine_neutral_choices: bool = True,
    totalbar: bool = True,
):
    """
    creates a dictionary with the compare_with answers as entries, each
    compare_with answer gets their own set of percentages corresponding
    to the number of people that answered the single_choice compare_with answer
    and how they answered the array_question.
    A Total bar is added if totalbar=True, and shows the answers to the array
    question, not separated by answers to single_choice question.
    The Total Bar should have the same results as the normal plot without
    comparison.
    """
    answer_dictionary = {}
    choices = array_question_data[1]
    if combine_neutral_choices:
        choices.append("all neutral choices")
    if totalbar:
        legend_sequence.append("Total")
    for answer in legend_sequence:
        if answer == "Total":
            question_data = array_question_data[0].iloc[:, :]
        else:
            question_data = array_question_data[0].iloc[
                np.where(answer == compare_with_data)[0], :
            ]
        indicator_matrix = []
        for row in np.asarray(question_data):
            indicator_matrix.append(
                [
                    x
                    if x in grouped_choices["left"]
                    else "nan"
                    if x in grouped_choices["center"]
                    else x
                    for x in row
                ]
            )
        indicator_matrix = np.array(indicator_matrix)
        participants_that_gave_answer = indicator_matrix.shape[0]
        answer_dictionary[answer] = []
        for column in np.transpose(indicator_matrix):
            if combine_neutral_choices:
                choice_count = [0] * (len(choices) - 1)
            else:
                raise NotImplementedError(
                    """
                                          only combined neutral choices
                                          possible at the moment
                                          """
                )
            count = 0
            for position in choice_count:
                choice_count[count] = np.round(
                    (
                        np.where(column == choices[count])[0].shape[0]
                        / participants_that_gave_answer
                        * 100
                    ),
                    decimals=2,
                )
                if choices[count] in grouped_choices["right"]:
                    choice_count[count] = -choice_count[count]
                count = count + 1

            # add one count for all neutral choices together to not overcrowd
            # the middle of the bar.

            if combine_neutral_choices:
                choice_count = choice_count + [
                    np.round(
                        (
                            np.where(column == "nan")[0].shape[0]
                            / participants_that_gave_answer
                            * 100
                        ),
                        decimals=2,
                    )
                ]
                # remove neither/nor, Does not apply, I don't want to answer
                # this question and 'No Answer' if neutral choices are combined
                # in last element
                count = 0
                new_choice_count = []
                for position in choice_count.copy():
                    if choices[count] in grouped_choices["center"]:
                        pass
                    else:
                        new_choice_count.append(position)
                    count = count + 1
                choice_count = new_choice_count
            answer_dictionary[answer].append(choice_count)
            if combine_neutral_choices:
                choices = [
                    choice
                    for choice in choices
                    if choice not in grouped_choices["center"]
                ]
    return answer_dictionary, choices


def calculate_bar_starts_from_data(
    column, choice, grouped_choices, percentage_groups, position_of_column
):
    if choice in grouped_choices["left"]:
        # add 0.5 neutral bar
        starts = column + percentage_groups[:, -1] * 0.5
        column_index = grouped_choices["left"].index(choice)
        if column_index == 0:
            if len(grouped_choices["left"]) == 3:
                starts = (
                    starts
                    + percentage_groups[:, position_of_column + 1]
                    + percentage_groups[:, position_of_column + 2]
                )
            elif len(grouped_choices["left"]) == 2:
                starts = starts + percentage_groups[:, position_of_column + 1]
            elif len(grouped_choices["left"]) == 1:
                pass
        elif column_index == 1:
            if len(grouped_choices["left"]) == 3:
                starts = starts + percentage_groups[:, position_of_column + 1]
            else:
                pass
    # add start points for positive bars
    if choice in grouped_choices["right"]:
        starts = np.array([0] * len(column)) - 0.5 * percentage_groups[:, -1]
        right_count = grouped_choices["right"].index(choice)
        if right_count == 1:
            starts = starts + percentage_groups[:, position_of_column - 1]
        elif right_count == 2:
            starts = (
                starts
                + percentage_groups[:, position_of_column - 1]
                + percentage_groups[:, position_of_column - 2]
            )
    if choice == "all neutral choices":
        starts = np.array([0] * len(column)) - 0.5 * column
    return starts
