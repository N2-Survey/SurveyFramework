import unittest
from n2survey.lime.survey import LimeSurvey


class TestLimeSurvey(unittest.TestCase):

    def test_plot(self):
        with self.assertRaises(NotImplementedError):
            lime_survey = LimeSurvey("./data/survey_structure.xml")
            lime_survey.plot('question', 'basic bar plot', figsize=(7,8))
            with self.assertRaises(TypeError):
                lime_survey.plot('question', 'not a plot')
                lime_survey.plot('question', "unavialble keyword")

if __name__ == '__main__':
    unittest.main()
