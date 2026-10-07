# Overview


### Setup

#### Cloning Repo
Navigate to a local directory where you would like to clone this repo, such as in a repos directory, which the following instructions will assume

```
cd repos

git clone https://github.com/rya000667/public-fantast-football-analytics.git

cd public-fantast-football-analytics
```

#### Setting up Local Development Environment
In the root of the repo from above, we will setup a virtual environment.  There are many ways to do this, this approach will demonstrate using pythons built in venv module and assume that your operating system has python configured as 'python'.  Note there are other means to configure such as py3, python3, etc.  If that is the case, replace python below with what you have configured.  Also, we will name the local virtual environment .venv, feel free to replace with your preferred name.

Note, this environment was built using python 3.14.7, so it is recommended to use that version or higher

```
python -m venv .venv
# to validate success, you should now see the command line as (.venv)

# install requirements
pip -r requirements.txt
```

### Code Formatting
We used black for formatting and linting for this project.  This can be run on the src/ directory and the specific notebook files we created

```
# Run linting on src/
black src/

# Run linting on notebooks
black expore-api-sports-notebook.ipynb
black 'Fantasy Football Metrics Core Analysis.ipynb'
```



### Creating PDF for Notebook
For this, we created a narrative jupyter notebook that we converted to PDF and removed the input code cells for space.
In addition to additional python modules like nbconvert being added to requirements.txt, we also had to intall an additional command line tool called pandoc that nbconvert called on.

```
# pandoc is needed by nbconvert to convert the markdown cells in the notebooks
# setup pandoc on mac
brew install pandoc

# setup pandoc on windows
winget install --id JohnMacFarlane.Pandoc -e
```

```
# Chromium is needed by nbconvert's to webpdf because this renders in HTML (where Chromium opens the page in HTML for nbconvert's conversion)
# Install Chromium for playwright
playwright install chromium
```

#### Generate the PDF of the Notebook
```
jupyter nbconvert --to webpdf --no-input 'Fantasy Football Metrics Core Analysis.ipynb' --output-dir PDFs --output fantasy-football-narrative
```




