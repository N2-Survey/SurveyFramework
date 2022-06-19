#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Jun  7 09:38:31 2022

@author: theflike
"""

from typing import Union

import matplotlib.pyplot as plt
import numpy as np

from .comparison_shared_functions import (
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
):

    """
    Plots correlations between array answers and the answers of
    single choice questions.
    """

    # for answer in compare_with_answers:
    y_labels = [entry for entry in plot_data_list[0][0]]
    grouped_choices = get_grouped_choices(
        options=plot_data_list[0][0][1], all_grouped_choices=DEFAULT_GROUPED_CHOICES
    )
    answer_dictionary = {}
    compare_with_data = plot_data_list[0][1]
    choices = plot_data_list[0][0][1]
    for answer in legend_sequence:
        question_data = plot_data_list[0][0][0].iloc[
            np.where(answer == compare_with_data)[0], :
        ]
        indicator_matrix = []
        for row in np.asarray(question_data):
            indicator_matrix.append(
                [
                    x
                    if x in grouped_choices["left"]
                    else 0
                    if x in grouped_choices["center"]
                    else x
                    for x in row
                ]
            )
        indicator_matrix = np.array(indicator_matrix)
        participants_that_gave_answer = indicator_matrix.shape[0]
        answer_dictionary[answer] = []
        for column in np.transpose(indicator_matrix):
            choice_count = [0] * len(choices)
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
            choice_count = choice_count + [
                np.round(
                    (
                        np.where(column == "0")[0].shape[0]
                        / participants_that_gave_answer
                        * 100
                    ),
                    decimals=2,
                )
            ]
            # remove single neutral choices
            remove_start = len(grouped_choices["left"])
            remove_stop = remove_start + len(grouped_choices["center"])
            print(choice_count)
            index_list = list(np.arange(remove_start, remove_stop, 1))
            count = 0
            filtered_choices = []
            for choice in choice_count:
                if count in index_list:
                    pass
                else:
                    filtered_choices.append(choice)
                count = count + 1
            choice_count = filtered_choices
            answer_dictionary[answer].append(choice_count)

    if totalbar:
        # add a total part to answer_dictionary, which should have the same
        # values as the s.plot(question)
        answer = "Total"
        question_data = plot_data_list[0][0][0].iloc[:, :]
        indicator_matrix = []
        for row in np.asarray(question_data):
            indicator_matrix.append(
                [
                    x
                    if x in grouped_choices["left"]
                    else 0
                    if x in grouped_choices["center"]
                    else x
                    for x in row
                ]
            )
        indicator_matrix = np.array(indicator_matrix)
        participants_that_gave_answer = indicator_matrix.shape[0]
        answer_dictionary[answer] = []
        for column in np.transpose(indicator_matrix):
            choice_count = [0] * len(choices)
            count = 0
            remove_indizes = []
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
                if choices[count] in grouped_choices["center"]:
                    remove_indizes.append(count)
                count = count + 1

            # add one count for all neutral choices together
            choice_count = choice_count + [
                np.round(
                    (
                        np.where(column == "0")[0].shape[0]
                        / participants_that_gave_answer
                        * 100
                    ),
                    decimals=2,
                )
            ]
            # remove single neutral choices
            remove_start = len(grouped_choices["left"])
            remove_stop = remove_start + len(grouped_choices["center"])
            print(choice_count)
            index_list = list(np.arange(remove_start, remove_stop, 1))
            count = 0
            filtered_choices = []
            for choice in choice_count:
                if count in index_list:
                    pass
                else:
                    filtered_choices.append(choice)
                count = count + 1
            choice_count = filtered_choices
            answer_dictionary[answer].append(choice_count)
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
        answer_dictionary, bar_width, bar_positions_per_answer=bar_positions
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
    )
    print(positionlist_per_answer)
    print(bar_positions_complete)
    print(y)
    print(answer_dictionary)
    brakk
    for answer in answer_dictionary:
        percentage_groups = answer_dictionary[answer]
        label = [answer] * len(percentage_groups[0])
        ax.barh(
            bar_positions_complete,
            widths,
            left=starts,
            height=bar_width,
            label=label,
            color=colors[position][index_response],
            **kwargs,
        )
    plt.yticks(bar_positions, y_labels)

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
