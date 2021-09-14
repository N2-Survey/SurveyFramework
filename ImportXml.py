# flake8: noqa
import re
import sys
from json import dump

from bs4 import BeautifulSoup

# import pandas as pd
# from collections import defaultdict


def read_questionnaire_structure(filepath: str, writefiles: bool):
    """
    Reads questionnaire structure XML file

    Args:
        filepath: A string with a path to a XML file with questionnaire structure
        writefiles: if True will dumps data to files as .json which can be opened \
                    by json.load(file) or pandas.read_json(file).
    Returns:
        A dict containing the questionnaire structure:
        {
            "sections": {
               {
                   "id":13901,
                   "title": "Demographics",
                   "info": "In this section, we will ask general questions about yourself \
                       and your doctoral project."
               },
               ....
            },
            "questions": {
                "name": "A1",
                "question": "What is your year of birth?",
                "description": "Please use the following format: 'xxxx' , e.g. 1989",
                "type": "category",
                "categories": {"I don't want to answer this question": 'A2',
                                ...
                                'Year of birth: ': 'A4other'},
                "subquestions": {
                    'E7a_SQ001': 'My supervisor is well informed about my field of research.',
                    'E7a_SQ002': 'My supervisor is available when I need advice.',
                    'E7a_SQ003': 'My supervisor is open to and respects my research ideas.',
                    'E7a_SQ004': 'My supervisor gives constructive feedback.',
                    ...},
                "section_id": 13901
            }
        }

    Raises:
        ValueError: Invalid XML file
        ValueError: Provided file has unexpected structure
    """

    def uniCodeRe(s) -> str:
        # '\u00a0','\u20ac', '\u00b2', '\u00a7'
        matched = ["\n", "\t", "\xa0"]
        # if you want to change the unicode
        # s_new = s.replace(u'\u2018', '"').replace(u'\u2019', '\'').replace(u'\u00f6', r'ö').replace(u'\u00fc', r'ü')
        # s_new = s
        res_s = re.sub("|".join(matched), "", s)
        return res_s

    def textParse(bsString) -> str:
        text = ""
        sps = BeautifulSoup(bsString, "html.parser").find_all("p")
        # sbs = BeautifulSoup(bsString, 'html.parser').find_all('b')
        for sp in sps:
            if bool(sp.string):
                text += uniCodeRe(sp.string)
        return text

    def findCategories(resp) -> dict:
        cates = dict()
        cats = resp.find_all("category")
        for cat in cats:
            cat_lab = cat.label.string
            cat_val = cat.value.string
            # A#other case
            if bool(cat.contingentQuestion):
                cat_val = cat.contingentQuestion.attrs["varName"]
                cat_lab = uniCodeRe(cat.contingentQuestion.find("text").get_text())
            cates[cat_lab] = cat_val
        return cates

    def findSubquestions(que) -> dict:
        res_sub = dict()
        subs = que.find_all("subQuestion")
        for sub in subs:
            res_sub[sub["varName"]] = sub.find("text").get_text()
        return res_sub

    def concatQuesitonText(ques) -> str:
        res_desc = ""
        for que in ques:
            res_desc += uniCodeRe(BeautifulSoup(que.string, "html.parser").get_text())
        return res_desc

    Ans = dict()
    try:
        f = open(filepath, "r")
    except OSError:
        print(f"{filepath} is an invalid xml file")
        sys.exit()

    soup = BeautifulSoup(f, "xml")
    secs = soup.find_all("section")
    res_sections = list()
    res_questions = list()
    for sec in secs:
        sec_id = sec.attrs["id"]
        sec_title = sec.sectionInfo.contents[3].string
        for info in sec.find_all("sectionInfo"):
            sec_text = info.find_all("text")
            text_p = ""
            for t in sec_text:
                text_p += textParse(t.string)
            sec_info = text_p
        res_sections.append({"id": sec_id, "title": sec_title, "info": sec_info})
        ques = sec.find_all("question")
        for que in ques:
            que_cat = {}
            que_sub = {}
            resps = que.find_all("response")
            que_que = uniCodeRe(
                BeautifulSoup(que.find("text").string, "html.parser").get_text()
            )

            if que.find("directive") is not None:
                que_descs = que.find("directive").find_all("text")
                que_desc = concatQuesitonText(que_descs)
            else:
                que_desc = ""

            for resp in resps:
                que_names = {
                    True: resps[0].attrs["varName"] + " multi answers",
                    False: resp.attrs["varName"],
                }
                que_name = que_names[len(resps) != 1]

                # if under question next level exist "format" means
                # it is a "longtext" question else "category" question
                if resp.category is None:
                    que_type = resp.format.string  # longtext
                    que_cat = {}
                    que_sub = {}
                else:
                    que_type = "catogory"
                    que_cat.update(findCategories(resp))
                    que_sub.update(findSubquestions(que))

            res_questions.append(
                {
                    "name": que_name,
                    "type": que_type,
                    "question": que_que,
                    "description": que_desc,
                    "categories": que_cat,
                    "sub_questions": que_sub,
                    "section_id": sec_id,
                }
            )

    Ans = {"section": res_sections, "questions": res_questions}

    if writefiles:
        with open("xml2json.dat", "w") as fw:
            dump(Ans, fw)
        with open("sections.dat", "w") as fs:
            dump(res_sections, fs)
        with open("quesitons.dat", "w") as fq:
            dump(res_questions, fq)

    return Ans


if __name__ == "__main__":
    dic = read_questionnaire_structure("./survey_structure.xml", True)
# with open('write_xml.dat', 'w') as fw:
#     dump(dic, fw)
# print(dic)
