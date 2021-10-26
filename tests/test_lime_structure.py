"""Test functions related to parsing of LimeSurvey files"""
import unittest

from bs4 import BeautifulSoup

from n2survey.lime.structure import (  # TODO: test _get_clean_string,; TODO: test _get_question_group_name,
    _parse_question,
    _parse_question_description,
    _parse_question_responses,
    _parse_question_subquestions,
    _parse_question_title,
    _parse_section,
    read_lime_questionnaire_structure,
)


class TestXMLSectionParsing(unittest.TestCase):
    """Test parsing <section> tags in an XML structure file"""

    def test_simple_section(self):
        """Test simple section parsing"""

        section = BeautifulSoup(
            """
            <section id="16">
                <sectionInfo>
                    <position>title</position>
                    <text>Group 1</text>
                    <administration>self</administration>
                </sectionInfo>
                <sectionInfo>
                    <position>before</position>
                    <text>This is Question Group 1</text>
                    <administration>self</administration>
                </sectionInfo>
                <question></question>
            </section>""",
            "xml",
        )
        self.assertDictEqual(
            _parse_section(section.section),
            {"id": 16, "title": "Group 1", "info": "This is Question Group 1"},
        )

    def test_multiply_info_sections(self):
        """Test simple section parsing"""

        section = BeautifulSoup(
            """
            <section id="16">
                <sectionInfo>
                    <position>title</position>
                    <text>Group 1</text>
                    <administration>self</administration>
                </sectionInfo>
                <sectionInfo>
                    <position>before</position>
                    <text>This is Question Group 1</text>
                    <administration>self</administration>
                </sectionInfo>
                <sectionInfo>
                    <position>after</position>
                    <text>This is Question Group 1</text>
                    <administration>self</administration>
                </sectionInfo>
                <question></question>
            </section>""",
            "xml",
        )
        self.assertDictEqual(
            _parse_section(section.section),
            {
                "id": 16,
                "title": "Group 1",
                "info": "This is Question Group 1 This is Question Group 1",
            },
        )

    def test_long_description(self):
        """Test a section with a long description"""

        section = BeautifulSoup(
            """
            <section id="13913">
                <sectionInfo>
                    <position>title</position>
                    <text>Supervision</text>
                    <administration>self</administration>
                </sectionInfo>
                <sectionInfo>
                    <position>before</position>
                    <text>&lt;p style="border:medium none;border-bottom:0cm none #000000;padding-bottom:0cm;margin:0cm 0cm .0001pt;padding:0cm;"&gt;&lt;b id="docs-internal-guid-90bd833e-7fff-2c78-398d-1ee9bdc67ae4"&gt;For the following questions, we would like to make the distinction between “formal” and “direct” supervisor clear: &lt;/b&gt;&lt;/p&gt;



                    “Formal” supervisor refers to the main advisor of your thesis as present in your committee.&lt;/b&gt;&lt;/p&gt;

                    “Direct” supervisor refers to the person you actually consult and discuss your project with on a more regular basis.&lt;/b&gt;&lt;/p&gt;



                    &lt;p style="border:medium none;border-bottom:0cm none #000000;padding-bottom:0cm;margin:0cm 0cm .0001pt;padding:0cm;"&gt;Section 4/8&lt;/p&gt;</text>
                    <administration>self</administration>
                </sectionInfo>
                <question></question>
            </section>""",
            "xml",
        )

        self.assertDictEqual(
            _parse_section(section.section),
            {
                "id": 13913,
                "title": "Supervision",
                "info": (
                    "For the following questions, "
                    "we would like to make the distinction between “formal” and “direct” "
                    "supervisor clear: “Formal” supervisor refers to the main advisor of "
                    "your thesis as present in your committee. “Direct” supervisor refers "
                    "to the person you actually consult and discuss your project with on a "
                    "more regular basis. Section 4/8"
                ),
            },
        )


class TestXMLQuestionParsing(unittest.TestCase):
    """Test parsing <question> tags in an XML structure file"""

    def test_question_title_parsing(self):
        question = BeautifulSoup(
            """<question>
        <text>&lt;p&gt;Do you have one of the following (multiple answers possible)?&lt;/p&gt;

            &lt;p style="border:medium none;border-bottom:0cm none #000000;padding-bottom:0cm;margin:0cm 0cm .0001pt;padding:0cm;"&gt; &lt;/p&gt;</text>
        </question>""",
            "xml",
        )
        question = question.question
        self.assertEqual(
            _parse_question_title(question),
            "Do you have one of the following (multiple answers possible)?",
        )

    def test_question_description_parsing(self):
        question = BeautifulSoup(
            """
            <question>
                <text>Is your formal supervisor your direct supervisor?</text>
                <directive>
                    <position>during</position>
                    <text>&lt;p&gt;“Formal” supervisor refers to the main advisor of your thesis as present in your committee.

                    “Direct” supervisor refers to the person you actually consult and discuss your project with on a more regular basis.&lt;/p&gt;</text>
                    <administration>self</administration>
                </directive>
                <response varName="E4"></response>
            </question>""",
            "xml",
        )
        question = question.question
        self.assertEqual(
            _parse_question_description(question),
            (
                "“Formal” supervisor refers to the main advisor of your thesis as present "
                "in your committee. “Direct” supervisor refers to the person you actually "
                "consult and discuss your project with on a more regular basis."
            ),
        )

    def test_choice_question_without_contingent(self):
        question = BeautifulSoup(
            """
            <question>
                <text>This is Group 1 Question 1 of type "5 point choice".</text>
                <directive>
                    <position>during</position>
                    <text>Help text for G1Q1

             </text>
                    <administration>self</administration>
                </directive>
                <response varName="G1Q1">
                    <fixed>
                    <category>
                        <label>1</label>
                        <value>1</value>
                    </category>
                    <category>
                        <label>2</label>
                        <value>2</value>
                    </category>
                    <category>
                        <label>3</label>
                        <value>3</value>
                    </category>
                    <category>
                        <label>4</label>
                        <value>4</value>
                    </category>
                    <category>
                        <label>5</label>
                        <value>5</value>
                    </category>
                    </fixed>
                </response>
                </question>""",
            "xml",
        )
        question = question.question

        choices = {"1": "1", "2": "2", "3": "3", "4": "4", "5": "5"}

        self.assertEqual(_parse_question_subquestions(question), [])
        self.assertEqual(
            _parse_question_responses(question),
            [
                (
                    {
                        "name": "G1Q1",
                        "format": None,
                        "length": None,
                        "label": None,
                        "choices": choices,
                    },
                    None,
                )
            ],
        )
        self.assertEqual(
            _parse_question(question),
            [
                {
                    "name": "G1Q1",
                    "label": 'This is Group 1 Question 1 of type "5 point choice".',
                    "format": None,
                    "choices": choices,
                    "question_group": "G1Q1",
                    "question_label": 'This is Group 1 Question 1 of type "5 point choice".',
                    "question_description": "Help text for G1Q1",
                    "type": "single_choice",
                }
            ],
        )

    def test_choice_question_with_contingent(self):
        question = BeautifulSoup(
            """
            <question>
                <text>My overall work is predominantly</text>
                <response varName="A3">
                    <fixed>
                    <category>
                        <label>Option 1</label>
                        <value>B1</value>
                    </category>
                    <category>
                        <label>Option 2</label>
                        <value>B2</value>
                    </category>
                    <category>
                        <label>Other</label>
                        <value>-oth-</value>
                        <contingentQuestion varName="A3other">
                        <text>Other</text>
                        <length>24</length>
                        <format>longtext</format>
                        </contingentQuestion>
                    </category>
                    </fixed>
                </response>
                </question>""",
            "xml",
        )
        question = question.question

        choices = {"B1": "Option 1", "B2": "Option 2", "-oth-": "Other"}

        self.assertEqual(_parse_question_subquestions(question), [])
        self.assertEqual(
            _parse_question_responses(question),
            [
                (
                    {
                        "name": "A3",
                        "format": None,
                        "length": None,
                        "label": None,
                        "choices": choices,
                    },
                    {
                        "name": "A3other",
                        "format": "longtext",
                        "length": "24",
                        "text": "Other",
                        "contingent_of_name": "A3",
                        "contingent_of_choice": "-oth-",
                    },
                )
            ],
        )
        self.assertEqual(
            _parse_question(question),
            [
                {
                    "name": "A3",
                    "label": "My overall work is predominantly",
                    "format": None,
                    "choices": choices,
                    "question_group": "A3",
                    "question_label": "My overall work is predominantly",
                    "question_description": "",
                    "type": "single_choice",
                },
                {
                    "name": "A3other",
                    "label": "My overall work is predominantly / Other",
                    "format": "longtext",
                    "contingent_of_name": "A3",
                    "contingent_of_choice": "-oth-",
                    "question_group": "A3",
                    "question_label": "My overall work is predominantly",
                    "question_description": "",
                    "type": "longtext",
                },
            ],
        )

    def test_question_without_choices(self):
        question = BeautifulSoup(
            """
            <question>
            <text>Some cool question</text>
            <response varName="Q1">
                <free>
                <format>text</format>
                <length>10</length>
                <label>What is good about it?</label>
                </free>
            </response>
            </question>
            """,
            "xml",
        )
        question = question.question

        self.assertEqual(_parse_question_subquestions(question), [])
        self.assertEqual(
            _parse_question_responses(question),
            [
                (
                    {
                        "name": "Q1",
                        "format": "text",
                        "length": "10",
                        "label": "What is good about it?",
                        "choices": None,
                    },
                    None,
                )
            ],
        )
        self.assertEqual(
            _parse_question(question),
            [
                {
                    "name": "Q1",
                    "label": "What is good about it?",
                    "format": "text",
                    "choices": None,
                    "question_group": "Q1",
                    "question_label": "Some cool question",
                    "question_description": "",
                    "type": "text",
                },
            ],
        )

    def test_multi_response_question(self):
        question = BeautifulSoup(
            """
            <question>
            <text>Some cool question</text>
            <response varName="Q1_R1">
                <free>
                <format>text</format>
                <length>10</length>
                <label>What is good about it?</label>
                </free>
            </response>
            <response varName="Q1_R2">
                <free>
                <format>text</format>
                <length>10</length>
                <label>What is bad about it?</label>
                </free>
            </response>
            </question>
            """,
            "xml",
        )
        question = question.question

        self.assertEqual(_parse_question_subquestions(question), [])
        self.assertEqual(
            _parse_question(question),
            [
                {
                    "name": "Q1_R1",
                    "label": "What is good about it?",
                    "format": "text",
                    "choices": None,
                    "question_group": "Q1",
                    "question_label": "Some cool question",
                    "question_description": "",
                    "type": "text",
                },
                {
                    "name": "Q1_R2",
                    "label": "What is bad about it?",
                    "format": "text",
                    "choices": None,
                    "question_group": "Q1",
                    "question_label": "Some cool question",
                    "question_description": "",
                    "type": "text",
                },
            ],
        )

    def test_question_with_subquestions(self):
        question = BeautifulSoup(
            """
            <question>
            <text>This is Group 2 Question 8 of type "array by column".</text>
            <directive>
                <position>during</position>
                <text>Help text for G2Q8</text>
                <administration>self</administration>
            </directive>
            <subQuestion varName="G2Q8_SQ001">
                <text>How do you rate this?</text>
            </subQuestion>
            <subQuestion varName="G2Q8_SQ002">
                <text>How do you rate that?</text>
            </subQuestion>
            <response varName="G2Q8">
                <fixed rotate="true">
                <category>
                    <label>Option 1</label>
                    <value>A1</value>
                </category>
                <category>
                    <label>Option 2</label>
                    <value>A2</value>
                </category>
                <category>
                    <label>Option 3</label>
                    <value>A3</value>
                </category>
                </fixed>
            </response>
            </question>
            """,
            "xml",
        )
        question = question.question
        choices = {"A1": "Option 1", "A2": "Option 2", "A3": "Option 3"}
        self.assertEqual(
            _parse_question_subquestions(question),
            [
                ("G2Q8_SQ001", "How do you rate this?"),
                ("G2Q8_SQ002", "How do you rate that?"),
            ],
        )
        self.assertEqual(
            _parse_question(question),
            [
                {
                    "name": "G2Q8_SQ001",
                    "label": "How do you rate this?",
                    "format": None,
                    "choices": choices,
                    "question_group": "G2Q8",
                    "question_label": 'This is Group 2 Question 8 of type "array by column".',
                    "question_description": "Help text for G2Q8",
                    "type": "array",
                },
                {
                    "name": "G2Q8_SQ002",
                    "label": "How do you rate that?",
                    "format": None,
                    "choices": choices,
                    "question_group": "G2Q8",
                    "question_label": 'This is Group 2 Question 8 of type "array by column".',
                    "question_description": "Help text for G2Q8",
                    "type": "array",
                },
            ],
        )


class TestXMLQuestionnarieParsing(unittest.TestCase):
    def test_test_survery_structure_file(self):
        structure = read_lime_questionnaire_structure(
            # "tests/data/test_survey_structure.xml"
            "data/survey_structure.xml"
        )
        self.assertEqual(len(structure["sections"]), 10)
        self.assertEqual(len(structure["questions"]), 453)

        structure = read_lime_questionnaire_structure(
            # "tests/data/test_survey_structure.xml"
            "data/survey_structure_2021.xml"
        )
        self.assertEqual(len(structure["sections"]), 13)
        self.assertEqual(len(structure["questions"]), 553)


if __name__ == "__main__":
    unittest.main()
