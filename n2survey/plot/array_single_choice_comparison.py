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
    count = 0
    fig, ax = plt.subplots()
    fig.set_tight_layout(True)
    for answer,sub_position in zip(legend_sequence,positionlist_per_answer):
        percentage_groups = np.array(answer_dictionary[answer])
        bar_positions = bar_positions_complete+sub_position
        column_count = 0
        for column,choice in zip(np.transpose(percentage_groups), choices):
            starts = column
            if choice in grouped_choices['left']:
                width = -column
                columns_to_add_to_starts = (
                    len(grouped_choices['left'])-
                    grouped_choices['left'].index(choice)
                    )-1
                i=1
                while columns_to_add_to_starts>0:
                    starts = starts+percentage_groups[:,count+i]
                    columns_to_add_to_starts=columns_to_add_to_starts-1
                    i = i+1
            print(starts)
            brakk
            # add start points for positive bars
            ax.barh(
                bar_positions,
                width=-1*widths,
                left=starts,
                height=1,
                label=answer,
            )
        count=count+1
    
    ax.legend(
        legend_sequence,
        loc=(0.1, 1),
        ncol=legend_columns,
        frameon=False,
        title=legend_title,
    )
    ax.invert_xaxis()
    plt.yticks(bar_positions_complete, y_labels)

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
    A Total bar is added if totalbar, and shows the answers to the array
    question, not separated by answers to single_choice question.
    The Total Bar should have the same results as the normal plot without
    comparison.
    """
    answer_dictionary = {}
    choices = array_question_data[1]
    if combine_neutral_choices:
        choices.append("all  neutral choices")
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
