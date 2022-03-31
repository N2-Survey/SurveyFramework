#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 15 21:28:19 2022

@author: theflike
"""
import numpy as np

__all__ = [
    "sort_data",
    "form_bar_positions",
    "form_single_answer_bar_positions",
    "filter_answer_sequence",
    "calculate_title_pad",
    "aspect_ratio_from_arguments",
]


def aspect_ratio_from_arguments(
    bar_positions_complete,
    positionlist_per_answer,
    theme,
    bar_width,
    answer_distance: float = None,
    bar_distance: float = None,
):
    """
    calculates the width of the plot, depending on total number of bars,
    distance between group of bars, bar thickness etc.
    """
    distance_between_answers = answer_distance or (0.5 * bar_width)
    distance_between_bars = bar_distance or (0.25 * bar_width)
    width = (
        len(bar_positions_complete) * len(positionlist_per_answer) * bar_width
        + distance_between_answers * len(bar_positions_complete)
        + distance_between_bars * len(positionlist_per_answer)
    ) * 0.4
    if theme["font_scale"] > bar_width:
        width = width / bar_width * 0.8 * theme["font_scale"]
    print(width)
    return width


def calculate_title_pad(labels, legend_columns, theme=None, legend_title: str = None):
    """
    calculates the height of the title above the plot depending on number
    of legend entries and number of columns that are reserved for the legend.
    """
    pad = int(len(labels) / legend_columns) * 20 + 20
    if legend_title:
        pad = pad + 20
    if theme:
        pad = pad * theme["font_scale"]
    return pad


def filter_answer_sequence(x, answer_sequence):
    """
    Remove answers from sequence that were supressed while creating x
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
    Sort lists x and y by comparing x and list sequence by rearranging x and y
    simoultaneously until x == sequence --> all entries in sequence have to
    also be in x
    at the moment each answer can only occure once in the plot, so if
    you want to add questions it is necessary to supress e.g. the 'no_answer'
    answer, else it would give an error. Can be improved in future.
    """
    indices = []
    for x_entry in x:
        if np.where(np.array(sequence) == x_entry)[0].shape[0] == 1:
            position = sequence.index(x_entry)
            indices.append(position)
        else:
            print(f"double bar: {x_entry}")
            raise NotImplementedError(
                """
                only single occurence of bars supported at the moment
                """
            )
    x_sorted = [entry for _, entry in sorted(zip(indices, x))]
    y_sorted = [entry for _, entry in sorted(zip(indices, y))]
    return x_sorted, y_sorted


def form_bar_positions(
    x,
    y,
    bar_width: float = 0.8,
    totalbar: bool = False,
    bar_positions: list = [],
    additional_question_start_indizes: list = [],
    distance_between_bars: float = 0.0,
):
    bar_positions_complete = bar_positions or [0]
    no_bars_per_answer = len(y)
    while len(bar_positions_complete) < len(x):
        bar_positions_complete.append(
            (
                max(bar_positions_complete)
                + distance_between_bars
                + bar_width * no_bars_per_answer
            )
        )
    return bar_positions_complete


def form_single_answer_bar_positions(y, bar_width, bar_positions_per_answer: list = []):
    """
    calculates the offset of multiple bars given in dictionary 'y'
    to a single x-position, depending on 'bar_width'
    """
    number_of_bars = len(y)
    space_per_answer = bar_width * number_of_bars
    if bar_positions_per_answer:
        while len(bar_positions_per_answer) < number_of_bars:
            bar_positions_per_answer.append(bar_positions_per_answer[-1] + bar_width)
        bar_positions_per_answer = np.array(bar_positions_per_answer)

    else:
        bar_positions_per_answer = np.arange(
            -space_per_answer / 2 + 0.5 * bar_width, space_per_answer / 2, bar_width
        )
    return bar_positions_per_answer
