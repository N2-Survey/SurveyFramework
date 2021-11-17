import unittest

from n2survey.lime import LimeSurvey


class BaseTestLimeSurvey2021Case(unittest.TestCase):
    """Base TestCase for testing survey files parsing using 2021 dummy"""

    @classmethod
    def setUpClass(cls):
        cls.structure_file = "data/survey_structure_2021.xml"
        cls.responses_file = "data/dummy_data_2021_codeonly.csv"
        # Default test questions
        cls.single_choice_column = "A6"
        cls.multiple_choice_column = "C3"
        cls.array_column = "B6"
        cls.free_column = "A8"
        # Read lime survey
        cls.survey = LimeSurvey(structure_file=cls.structure_file)
        cls.survey.read_responses(responses_file=cls.responses_file)

    @classmethod
    def tearDownClass(cls):
        cls.structure_file = None
        cls.responses_file = None
        cls.single_choice = None
        cls.multiple_choice = None
        cls.array = None
        cls.free = None
        cls.survey = None
