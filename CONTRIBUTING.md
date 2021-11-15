:+1::tada: First off, thanks for contributing! :tada::+1:

The following is a set of guidelines and instructions for contributing to the :snake:`Python` N2 Survey Framework.

# Workflow

1. Take an issue from the [issues list](https://github.com/N2-Survey/SurveyFramework/issues)(or the coordinator of your group will give you one)
2. Assign the issue to yourself (or the coordinator of your group will do it)
3. Work on your issue localy:
```bash
# update `main` branch:
git checkout main
git pull

# Create a new branch for your issue
git checkout -b <issue number>-<issue description>

# Do your changes
...

# Push your changes to GitHub
git push --set-upstream origin <your branch name>
```
4. Submit a PR and put your coordinator to reviewers

# Reporting Bugs and Submitting Suggestions

* Ensure that it was not already reported/suggested.
* If it was not, open a new issue. Be sure to include a title and clear description, as much relevant information as possible, and a code sample demonstrating the expected behavior that is not occurring.
* Include minimal working example.

# Setting up the project
Before starting your contribution it is important to setup the project properly, so the rest of the work goes smoothly. Here is some information to help you with that.
The instuctions bellow assume that you already have your `git` installed (see [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)). And aware of virtual environments (see [here](https://docs.python.org/3/tutorial/venv.html#virtual-environments-and-packages)).

## Linux / WSL (Windows Subsystem for Linux)
1. Install prerequisites (skip if you already have it):
  - `pyenv` - see the [instructions](https://github.com/pyenv/pyenv#installation)
  - `poetry` - see the [instructions](https://python-poetry.org/docs/master/#osx--linux--bashonwindows-install-instructions)
  - `git` - see [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)

2. Setup the project

```bash
# Clone the project
git clone https://github.com/N2-Survey/SurveyFramework.git

# Go to the project folder
cd SurveyFramework

# Install all dependencies
poetry install

# Activate the virtual environment
poetry shell

# Add pre-commit hooks (optional)
pre-commit install
```

3. Done!:tada:


## Windows
1. Install prerequisites (skip if you already have it):
  - `conda` - see the [anaconda](https://www.anaconda.com/products/individual-d)
  - `git` - see [here](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git)
  - `poetry` - see the [instructions](https://python-poetry.org/docs/master/#windows-powershell-install-instructions). **NOTE**: Most probably, you will have to add `%USERPROFILE%\AppData\Roaming\Python\Scripts` to your `PATH`. For that, *Control Panel>User Accounts>User Accounts>Change my environment variables>Edit...(under User variables for <username>)* (see [here](http://www.kscodes.com/misc/how-to-set-path-in-windows-without-admin-rights/))

2. In your PowerShell (with `conda`)
```bash
# Clone the project
git clone https://github.com/N2-Survey/SurveyFramework.git

# Go to the project folder
cd SurveyFramework

# Create a virtual env for the project
conda create -n n2survey python=3.9

# Activate the virtual environment
conda activate n2survey

# Install all dependencies
poetry install

# Add pre-commit hooks (optional)
pre-commit install
```

3. Done!:tada:

## MacOS
TBD
  
# Default questions for testing:

Single choice: A6
  
Multiple choice: C3
  
Array: B6

Free: A8