# Overview


### Setup

#### Cloning Repo
Navigate to a local directory where you would like to clone this repo, such as a `repos` directory, which the following instructions will assume. Run these in a terminal (Terminal on Mac, PowerShell on Windows, or the terminal built into VS Code).

```
cd repos

git clone https://github.com/rya000667/public-fantast-football-analytics.git

cd public-fantast-football-analytics
```

#### Setting up Local Development Environment
From the root of the repo (the folder containing `requirements.txt`), we will set up a virtual environment. There are many ways to do this; this approach uses Python's built-in venv module and assumes your operating system has Python configured as `python`. Other setups use `py` or `python3`; if that is the case, replace `python` below with what you have configured. We will name the local virtual environment `.venv`, but feel free to use your preferred name.

Note, this environment was built using Python 3.13, so it is recommended to use that version or higher.

**1. Create the virtual environment**

```
python -m venv .venv
```

This command prints nothing when it succeeds. It silently creates a `.venv` folder in the current directory. The `(.venv)` prefix on your command line only appears after you activate the environment in the next step.

**2. Activate the virtual environment**

```
# Mac/Linux
source .venv/bin/activate

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Command Prompt (cmd)
.venv\Scripts\activate.bat
```

You should now see `(.venv)` at the start of your command line. You will need to re-activate the environment each time you open a new terminal, and you must run all of the remaining commands in this README with it active.

*Windows PowerShell only:* if activation fails with "running scripts is disabled on this system", run the following once, then activate again:

```
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**3. Install requirements**

```
pip install -r requirements.txt
```

### Code Formatting
We used black for formatting this project. It can be run on the `src/` directory and on the specific notebook files we created. Running black on notebooks requires the Jupyter extra (`pip install "black[jupyter]"`), unless it is already in `requirements.txt`.

```
# Format src/
black src/

# Format notebooks
black explore-api-sports-notebook.ipynb
black 'Fantasy Football Metrics Core Analysis.ipynb'
```



### Creating PDF for Notebook
For this, we created a narrative Jupyter notebook that we converted to PDF, removing the input code cells for space.
In addition to Python modules like nbconvert being added to `requirements.txt`, we also had to install an additional command line tool called pandoc that nbconvert calls on, and Chromium (through Playwright) for the PDF rendering.

```
# pandoc is needed by nbconvert to convert the markdown cells in the notebooks
# setup pandoc on mac
brew install pandoc

# setup pandoc on windows
winget install --id JohnMacFarlane.Pandoc -e
```

```
# Chromium is needed by nbconvert's webpdf exporter because this renders in HTML
# (Chromium opens the page in HTML for nbconvert's conversion)
# Install Chromium for playwright (run with the virtual environment active)
playwright install chromium
```

If `jupyter` or the `webpdf` exporter is not found, make sure the virtual environment is active and that the extras are installed:

```
pip install jupyter "nbconvert[webpdf]"
```

#### Generate the PDF of the Notebook

**Mac/Linux**

```
jupyter nbconvert --to webpdf --no-input 'Fantasy Football Metrics Core Analysis PDF Source.ipynb' --output-dir PDFs --output fantasy-football-narrative
```

**Windows**

On Windows, the command above fails with a `NotImplementedError` from `asyncio.create_subprocess_exec`. This happens because the Jupyter command line wrapper switches Python to an asyncio event loop that cannot launch the subprocess Playwright needs. To get around it, use the `convert_to_pdf.py` script in the root of this repo, which skips the command line wrapper and sets the correct event loop before converting:

```
python convert_to_pdf.py
```

The script contains the following:

```python
import asyncio
import sys
from pathlib import Path

from nbconvert import WebPDFExporter

NOTEBOOK = "Fantasy Football Metrics Core Analysis.ipynb"
OUT_DIR = Path("PDFs")
OUT_NAME = "fantasy-football-narrative"

# Set this AFTER imports, right before converting, so nothing overrides it
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

exporter = WebPDFExporter()
exporter.exclude_input = True  # same as --no-input

body, resources = exporter.from_filename(NOTEBOOK)

OUT_DIR.mkdir(exist_ok=True)
out_path = OUT_DIR / f"{OUT_NAME}.pdf"
out_path.write_bytes(body)
print(f"Wrote {out_path}")
```

Either way, the PDF is written to `PDFs/fantasy-football-narrative.pdf`.

*Fallback (no Playwright needed):* export to HTML, then print it to PDF from a browser.

```
jupyter nbconvert --to html --no-input 'Fantasy Football Metrics Core Analysis.ipynb' --output-dir PDFs --output fantasy-football-narrative
```

Open `PDFs/fantasy-football-narrative.html` in Chrome or Edge, press `Ctrl+P`, choose "Save as PDF", and enable "Background graphics".

### Troubleshooting
- **`jupyter` is not recognized:** the virtual environment is not active in this terminal. Activate it (see Setup, step 2).
- **PowerShell says running scripts is disabled:** run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.
- **Chromium "executable doesn't exist":** run `playwright install chromium` with the virtual environment active.
- **Odd permission errors while installing on Windows:** if the repo lives inside OneDrive, file syncing can interfere with `.venv`. Consider moving the repo outside OneDrive or excluding `.venv` from syncing.

