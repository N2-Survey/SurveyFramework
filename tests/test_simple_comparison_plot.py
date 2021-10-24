from simple_comparison_plot import assemble_data_process, multi_bar_to_one_compare
from structure import read_lime_questionnaire_structure

# sys.path.insert(0, "/N2_Survey/SurveyFramework/n2survey/plot")
# sys.path.insert(0, "/N2_Survey/SurveyFramework/n2survey/lime")

"""
Laushir, here is some example for testing the results.
you can change any column name for single or multiple
columns comparison.
(as following the comment part)

goodluck, dron.
"""

structure_xml = read_lime_questionnaire_structure("../data/test_Oct.xml")
dim_xs, dim_y, recast_df = assemble_data_process(
    "../data/test_Oct.csv",
    structure_xml,
    # [("B7", False, True), ("A00", True, False)],
    [("A7", False, True)],
    ("A6", True),
    replace_name_dict_ind={
        "I don't want to answer this question": "NO COMMENT",
        "I don’t want to answer this question": "NO COMMENT",
        "Gender diverse (Gender-fluid)": "GD",
        "Other gender representations:": "Other",
    },
    replace_name_dict_col={
        "I don’t want to answer this question": "No Comment",
        "I don't want to answer this question": "No Comment",
        "Yes, it is okay for me and I agree with the data protection regulations for these sensitive questions": "Yes, dege",
        "No, I prefer not to see them": "No, budegir",
    },
)
multi_bar_to_one_compare(
    dim_xs,
    dim_y,
    recast_df,
    save_figure="../data/new_only_graph0.png",
    give_title="laushir, bai leener, kutree zhe. dron !",
    legend_location="upper center",
    # set_location=[1, 2, 3, 5.5, 6.5, 7.5, 8.5, 9.5, 11.5, 12.5, 15],
    set_location=[0, 1, 2, 3, 5, 6, 7, 8],
    color=[
        "royalblue",
        "steelblue",
        "cornflowerblue",
        "dodgerblue",
        "purple",
        "lightsteelblue",
        "slategrey",
        # "deepskyblue",
        # "darkmagenta",
    ],
)
