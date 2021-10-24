import sys

from bar_plot import bar_plot, extract_data
from structure import read_lime_questionnaire_structure

sys.path.insert(0, "/N2_Survey/SurveyFramework/n2survey/lime")

sys.path.insert(0, "/N2_Survey/SurveyFramework/n2survey/plot")


"""
Laushir, here is some example for test bar_plot.
and you can change the column name to whatever
you want.
Notice some warnings will provide some useful info.

goodluck, dron.
"""


structure_dict = read_lime_questionnaire_structure("../data/test_Oct.xml")
ser = extract_data("../data/test_Oct.csv", "C8")  # also 'A00', 'A6', 'A3' what else...
bar_plot(
    ser=ser,
    col_name="C8",
    structure_dict=structure_dict,
    color="pink",
    display_noanswer=True,
    save_fig="../data/bar_img21.png",
    replace_name_dict={
        "I don’t want to answer this question": "No Comment",
        "I don't want to answer this question": "No Comment",
        "More than 30 days": ">30 days",
    },
    #   'Gender diverse (Gender-fluid)':"Gender diverse",
    #   'Other gender representations:': 'Other'},\
    give_title="Holidays",
    give_y_label="DeGene",
    threshold=0.1,
)
print(f"{'finished'}")
