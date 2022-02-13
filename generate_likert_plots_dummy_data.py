import os

import matplotlib.pyplot as plt

from n2survey import LimeSurvey
from n2survey.plot import likert_bar_plot

# since its still undecided which kwargs should be passed to the LimesSurvey.plot method I didn't want to change the current
# kwargs of the plot method. To however show, what is currently possible with the Likert plot functionalities I've added
# some dummy function here to show different settings for the Likert plot.
DEFAULT_THEME = {
    "context": "notebook",
    "style": "darkgrid",
    "palette": "Blues",
    "font": "sans-serif",
    "font_scale": 1,
    "color_codes": True,
    "rc": {"figure.figsize": (12, 12), },
}


def likert_plot_all_kwargs(
    survey,
    question,
    theme=DEFAULT_THEME,
    grouped_questions=None,
    grouped_choices=None,
    sort_questions_by_choices="left",
    display_no_answer=False,
    display_title=True,
    axis_max_value=None,
    **kwargs,
):
    theme = theme.copy()
    theme.update(kwargs)

    counts_df = survey.count(question, labels=True, percents=False, add_totals=True)
    counts_df.loc["Total", "Total"] = survey.responses.shape[0]
    if not display_no_answer:
        try:
            counts_df = counts_df.drop("No Answer")
        except KeyError:
            pass

    if display_title:
        title_question = survey.get_label(question)
    else:
        title_question = None

    fig, ax = likert_bar_plot(
        counts_df,
        theme=theme,
        grouped_questions=grouped_questions,
        grouped_choices=grouped_choices,
        sort_questions_by_choices=sort_questions_by_choices,
        title_question=title_question,
        bar_spacing=0.2,
        bar_thickness=0.4,
        group_spacing=1,
        calc_fig_size=True,
        x_axis_max_values=axis_max_value,
    )
    fig.show()


if __name__ == "__main__":

    INPUT_PATH = "./data"
    XML_FILE_NAME = "survey_structure_2021.xml"
    CSV_FILE_NAME = "dummy_data_2021_codeonly.csv"
    OUTPUT_PATH = "./figures_dummy/"

    survey = LimeSurvey(os.path.abspath(os.path.join(INPUT_PATH, XML_FILE_NAME)))
    survey.read_responses(os.path.abspath(os.path.join(INPUT_PATH, CSV_FILE_NAME)))

    # clean up naming in dummy data
    # "I don’t want to answer this question" instead of "I don’t want to answer" so the default sorted choices can be used
    survey.responses = survey.responses.replace(
        to_replace="I don’t want to answer",
        value="I don’t want to answer this question",
    )
    is_dict = [isinstance(choices, dict) for choices in survey.questions.choices.values]
    survey.questions.loc[is_dict, "choices"] = survey.questions.choices[is_dict].apply(
        lambda x: {
            k: (
                "I don’t want to answer this question"
                if v == "I don’t want to answer"
                else v
            )
            for k, v in x.items()
        }
    )

    # group questions by sections
    question_groups = survey.questions["question_group"].copy()
    question_groups["section"] = survey.questions["question_group"].apply(
        lambda x: x[0]
    )
    if False:
        # plot all questions with default settings and save for visualization
        for i, (section_label, question_labels) in enumerate(
            question_groups.groupby("section").groups.items()
        ):
            # switch output folder to save plots in subfolders named as the section they belong to
            survey.output_folder = os.path.join(OUTPUT_PATH, section_label)
            if not os.path.exists(survey.output_folder):
                os.makedirs(survey.output_folder)
            for q_label in question_groups[question_labels].unique().tolist():
                question_type = survey.get_question_type(q_label)
                if question_type == "array" and survey.get_choices(q_label) is not None:
                    survey.plot(
                        q_label, save=q_label, palette=None,
                    )

    # plot example array question with different settings

    # I've selected not the default array question here since B6
    # contains only 3 questions and some features are difficult to show then
    EXAMPLE_QUESTION = "E7a"

    # DISPLAY TITLE #
    print("Display / Hide Title")
    survey.plot(EXAMPLE_QUESTION, save=False, palette=None)
    likert_plot_all_kwargs(survey, EXAMPLE_QUESTION, display_title=False, palette=None)
    plt.show()

    # COLORING #
    print("Plot with different colors")

    # use own palette implementation (default of Likert plot)
    survey.plot(EXAMPLE_QUESTION, save=False, palette=None)
    # plot with seaborn default sequential palette
    survey.plot(EXAMPLE_QUESTION, save=False, palette="Blues")
    # plot with seaborn diverging palette
    survey.plot(EXAMPLE_QUESTION, save=False, palette="icefire")
    plt.show()

    # GROUP QUESTIONS #
    print("Group questions to blocks")
    survey.plot(EXAMPLE_QUESTION, save=False, palette=None)

    questions = survey.get_question(EXAMPLE_QUESTION).label.values
    grouped_questions = [[questions[0]], [*questions[1:]]]
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, grouped_questions=grouped_questions, palette=None
    )

    grouped_questions = [[questions[0]], [*questions[1:4]], [*questions[4:]]]
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, grouped_questions=grouped_questions, palette=None
    )
    plt.show()

    # SORT QUESTIONS #
    print(
        "Sort bars (questions) by the fraction of responses that where assigned "
        "to be plotted on the left or the right side of the scale."
    )
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, sort_questions_by_choices="left", palette=None
    )
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, sort_questions_by_choices="right", palette=None
    )
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, sort_questions_by_choices="no_sorting", palette=None
    )
    plt.show()

    # GROUP RESPONSES #
    print(
        "Assign the choices to the groups 'left', 'center' and 'right'. "
        "By assigning each choice to a plot location also possible to not plot them by not assigning them at all."
    )
    survey.plot(EXAMPLE_QUESTION, palette=None, save=False)

    # swap left and right compared to default plot
    grouped_choices = {
        "right": ["Fully agree", "Partially agree"],
        "center": [
            "Neither agree nor disagree",
            "I don’t know",
            "I don’t want to answer this question",
            "No Answer",
        ],
        "left": ["Partially disagree", "Fully disagree"],
    }
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, grouped_choices=grouped_choices, palette=None
    )
    # remove all center choices
    grouped_choices = {
        "left": ["Fully agree", "Partially agree"],
        "center": [],
        "right": ["Partially disagree", "Fully disagree"],
    }
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, grouped_choices=grouped_choices, palette=None
    )

    # remove some center choices
    grouped_choices = {
        "left": ["Fully agree", "Partially agree"],
        "center": ["Neither agree nor disagree"],
        "right": ["Partially disagree", "Fully disagree"],
    }
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, grouped_choices=grouped_choices, palette=None
    )
    plt.show()

    # SORT AND GROUP QUESTIONS #
    print(" Sort and group questions")
    grouped_choices = {
        "left": ["Fully agree", "Partially agree"],
        "center": [],
        "right": ["Partially disagree", "Fully disagree"],
    }
    questions = survey.get_question(EXAMPLE_QUESTION).label.values
    grouped_questions = [[questions[0]], [*questions[1:4]], [*questions[4:]]]
    likert_plot_all_kwargs(
        survey,
        EXAMPLE_QUESTION,
        grouped_questions=grouped_questions,
        palette=None,
        grouped_choices=grouped_choices,
        sort_questions_by_choices="left",
    )
    likert_plot_all_kwargs(
        survey,
        EXAMPLE_QUESTION,
        grouped_questions=grouped_questions,
        palette=None,
        grouped_choices=grouped_choices,
        sort_questions_by_choices="right",
    )
    likert_plot_all_kwargs(
        survey,
        EXAMPLE_QUESTION,
        grouped_questions=grouped_questions,
        palette=None,
        grouped_choices=grouped_choices,
        sort_questions_by_choices="no_sorting",
    )
    plt.show()

    print("Display no answers / or filter them")
    survey.plot(EXAMPLE_QUESTION, palette=None, save=False)
    likert_plot_all_kwargs(
        survey, EXAMPLE_QUESTION, display_no_answer=True, palette=None
    )
    plt.show()

    # SET AXIS SCALE #
    print("Crop axis to a fixed percentage")
    survey.plot(EXAMPLE_QUESTION, palette=None, save=False)
    likert_plot_all_kwargs(survey, EXAMPLE_QUESTION, axis_max_value=50, palette=None)
    plt.show()
