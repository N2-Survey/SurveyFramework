from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import seaborn as sns

__all__ = ["simple_comparison_plot"]

def get_percentages(array, threshold=0, answer_supress = False, totalbar = False):
    # get possible combinations
    (combi, 
     no_of) = np.unique(array.astype(str), return_counts = True, axis=0)
    if totalbar:
        total_combi = np.full((totalbar[0].shape[0],1),"Total")
        total_combi = np.append(total_combi, np.reshape(totalbar[0], newshape=(-1,1)), axis=1)
        combi = np.append(total_combi, combi, axis=0)
        no_of = np.append(totalbar[1],no_of)
    # calculate percentages of x
    percentage = {}
    for answer in combi[:,0]:
        answer_rows = np.where(combi[:,0] == answer)
        percentage[answer] = np.append(
            np.reshape(combi[answer_rows, 1], newshape = (-1,1)),
            np.reshape(
                np.round(no_of[answer_rows]/sum(no_of[answer_rows])*100, 
                         decimals=1), newshape = (-1,1)
                ), axis=1
            )
    return percentage
    
def form_x_and_y(df, totalbar=False):
    PERCENTAGE = get_percentages(df, totalbar=totalbar)
    x = []
    y = []
    for entry in PERCENTAGE:
        x.append(entry)
        y.append(PERCENTAGE[entry])
    return x, y

def simple_comparison_plot(df,
                           answer_supress = False,
                           theme: Optional[Dict] = None,
                           titles: Optional[list] = None,
                           totalbar = False,
                           no_answers = False,
                           hide_titles = False,
                           spacing_bar = False,
                           show_percents = True,
                           threshold_percentage = 0,
                           bar_width = 0.8
                           ):
    (x,y) = form_x_and_y(df, totalbar=totalbar)
        
    # %% Prepare figure
    fig, ax = plt.subplots()
    fig_width, _ = fig.get_size_inches()
    # %% plot
    q2_answers = []
    percentages = []
    for entry in y:
        q2_answers.append(entry[:,0])
        percentages.append(entry[:,1].astype(np.float64))
    all_answers = np.unique(np.concatenate(np.array(q2_answers)))
    percentage_all = []
    for (percentage,
         q2_answer) in zip(percentages, q2_answers):
        count=0
        percentage_all_single = []
        for answer in all_answers:
            if answer in q2_answer:
                percentage_all_single.append(percentage[count])
                count = count+1
            else:
                percentage_all_single.append(0)
        percentage_all.append(percentage_all_single.copy())
    # plot comparison bars
    bottom = 0
    count=0
    for answer,percentage in zip(all_answers, np.transpose(np.array(percentage_all))):
        ax.bar(x, percentage, bottom=bottom, label=answer,
               width=bar_width)
        bottom = bottom + percentage
        labels = percentage.astype(str)
        labels[np.where(labels.astype(np.float64) <= threshold_percentage)]=''
        ax.bar_label(ax.containers[count], labels, fmt='%s',
                     label_type='center')
        count = count+1
    labels = all_answers
    ax.legend(labels, bbox_to_anchor=([0.1, 1, 0, 0]), ncol=2,
               frameon=False)
    # scale
    plt.setp(ax.get_xticklabels(), rotation=30,
             horizontalalignment='right')
    # figure settings
    fig.tight_layout()
    return fig, ax