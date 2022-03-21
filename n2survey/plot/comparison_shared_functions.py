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
]


def calculate_title_pad(labels, legend_columns, legend_title: str = None):
    pad = int(len(labels) / legend_columns) * 20 + 20
    if legend_title:
        pad = pad + 20
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
    bar_width=0.8,
    totalbar=None,
    bar_positions=[],
    additional_question_start_indizes=[],
):
    bar_positions_complete = bar_positions or [0]
    no_bars_per_answer = len(y)
    while len(bar_positions_complete) < len(x):
        bar_positions_complete.append(
            max(bar_positions_complete) + 1 + bar_width * no_bars_per_answer
        )
    return bar_positions_complete


def form_single_answer_bar_positions(y, bar_width):
    """
    calculates the offset of multiple bars given in dictionary 'y'
    to a single x-position, depending on 'bar_width'
    """
    number_of_bars = len(y)
    space_per_answer = bar_width * number_of_bars
    bar_positions_per_answer = np.arange(
        -space_per_answer / 2 + 0.5 * bar_width, space_per_answer / 2, bar_width
    )
    return bar_positions_per_answer
