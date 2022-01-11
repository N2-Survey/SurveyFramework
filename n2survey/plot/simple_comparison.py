from typing import Dict, Optional, Tuple, Union

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import numpy as np
import seaborn as sns

__all__ = ["simple_comparison_plot"]

def form_xs_and_ys(data_dfs):

    return xs, ys

def simple_comparison_plot(data_dfs,
                           dimensions = False,
                           answer_supress = False,
                           theme: Optional[Dict] = None,
                           titles: Optional[list] = None,
                           totalbar = False,
                           no_answers = False,
                           hide_titles = False,
                           spacing_bar = False
                           ):
    # %% additional parameters from bar.py
    # Additional parameters to provide in `sns.barplot`
    additional_params = {}

    palette = None
    if theme is not None:
        sns.set_theme(**theme)
        palette = theme.get("palette", None)

    # HOTFIX: For some reason, setting "palette" in `set_theme`
    # does not apply the palette. To make it work, we have to provide
    # it directly to `barplot` function
    if palette is not None:
        additional_params = {"palette": palette}
        
    # %% dimensions of plot
    if dimensions:
        (width,height) = dimensions
    else:
        width = len(xs[0])*8
        height = len(xs)*9
        
    # %% create figure
    
    fig = plt.figure()
    fig.set_size_inches(width,height)
    
    # %% plotting
    
    for xrow,yrow in zip(xs,ys):
        for (x,y) in zip(xrow,yrow):
            print(y)
            ax = fig.add_subplot(
                len(xs), len(xrow), (xs.index(xrow)+1+xrow.index(x)*len(xs))
                )
            sns.barplot(x=x, y=y, ci=None, ax=ax, **additional_params)
            # scale
            #ax.autoscale()
            #ax.set_autoscale_on(True)
            plt.setp(ax.get_xticklabels(), rotation=30, horizontalalignment='right')
            

    # figure settings
    fig.tight_layout()
    return fig, ax