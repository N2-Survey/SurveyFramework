# N2 Survey Framework
Python framework to analyze the N2 Network surveys.


# Install

1. Create virtual env (python 3.9)
   For example use anaconda:
      a) install anaconda. Instruction for installations can be found here: https://docs.anaconda.com/anaconda/install/
      b) create a conda environment: 
         conda create -n n2survey python=3.9
      c) activate your conda environment:
         conda activate n2survey
      d) Follow the step below
2. Install the package: `python -m pip install git+https://github.com/N2-Survey/SurveyFramework`

# Usage 

```python
# Imports
from n2survey import LimeSurvey

# Read the structure file
s = LimeSurvey("./data/survey_structure_2021.xml")

# Read responses
# NOTE: Responses are provided in CODES only
s.read_responses("./data/dummy_data_2021_codeonly.csv")

# Plot a question
s.plot("A6")

# Plot a question and save it
s.plot("A6", save=True)

# Change output directory
s.output_folder = "Some folder where images will be saved"

# Customize theme
s.theme["rc"]["figure.figsize"] = (6,6)
s.theme["palette"] = "Reds"
s.plot("A6")

# Print some summary
s.count("A6", labels=True)
s.count("A6", labels=True, percents=True)
s.count("B1", labels=True)
s.count("B6", labels=True)
s.count("B6", labels=True, add_totals=True)

# Get all responses
s.responses

# Get all questions
s.questions

# Get responses for a question
s.get_responses("A6", labels=True)
s.get_responses("A6", labels=True, drop_other=True)
s.get_responses("B1", labels=True)

# Get questions starting with "A"..
s.questions[s.questions.index.str.startswith("A")]

# Get choices for a question
s.get_choices("A6")
```
