[![DOI](https://zenodo.org/badge/403667928.svg)](https://zenodo.org/badge/latestdoi/403667928)



# N2 Survey Framework
Python framework to analyze the N2 Network surveys.


# Install

1. Create virtual env (python 3.9) <br /> 
   For example use anaconda:
      - install anaconda. Instruction for installations can be found [here](https://docs.anaconda.com/anaconda/install):   <br /> 
        Please install the full anaconda version and not the miniconda
      - create a conda environment: ```conda create -n n2survey python=3.9```
      - activate your conda environment: ```conda activate n2survey```
      - Install git: ```conda install git```
      - Follow the step below
2. Install the package: `python -m pip install git+https://github.com/N2-Survey/SurveyFramework`

# Usage 

Alternative to instructions below: Use the jupyter-notebook described [here](https://docs.google.com/document/d/1HkuJMsaKj77H-GgjQmFrUXJ0El93ksDBSWYVJnH98lw/edit?usp=sharing):

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

# Get responses for a question, returning a pd.DataFrame
s.get_responses("A6", labels=True)
s.get_responses("A6", labels=True, drop_other=True)
s.get_responses("B1", labels=True)
# Alternatively, get responses for one or more questions
# returning a LimeSurvey object, to perform follow-up operations
s2 = s[["A6", "B6"]]

# Get questions starting with "A"..
s.questions[s.questions.index.str.startswith("A")]

# Get choices for a question
s.get_choices("A6")

# Filter by answers to specific questions
# e.g. entries where the response to Question A3 is A5
s_filtered = s[s.responses["A3"] == "A5"]
# Alternatively, apply multiple filter conditions
# e.g. entries where the response to Question A6 is A3
# OR that to Question B2 is A5
s_filtered = s.query("A6 == 'A3' | B2 == 'A5'")
# Both methods return a LimeSurvey object, upon which
# similar operations can be performed again and plot 
# functions can also be called
