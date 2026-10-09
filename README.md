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
black expore-api-sports-notebook.ipynb
black 'Fantasy Football Metrics Core Analysis.ipynb'
black 'Fantasy Football Metrics Core Analysis PDF Source.ipynb'
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


# Exploratory Data Analysis
## Introduction

Fantasy football is a game in which participants act as team managers. Each manager "drafts" a roster of real NFL players, taking turns picking from the same pool of players, much like picking teams on a playground. Each week, the players on a manager's roster earn points based on how they perform in their real NFL games, such as yards gained, touchdowns scored, and passes caught. A manager's team is scored against another manager's team each week, and the better score wins.

Week-to-week management matters, but the draft is where most of a team's strength is built. A strong draft provides consistent scoring every week and enough depth to absorb injuries to key players.

Most advice on who to draft comes from expert rankings and intuition or from average draft position (ADP), which simply shows where other managers usually pick a player. This analysis instead uses data to build a draft strategy.

**Key terms**

- **Positions:** Offensive players fall into four main groups. Quarterbacks (QB) throw the ball. Running backs (RB) carry it. Wide receivers (WR) and tight ends (TE) catch it.
- **Scoring format:** Leagues differ in how they award points for catches. In **PPR** (points per reception) leagues, a player earns 1 point for every catch on top of points for yards and touchdowns. In **non-PPR** (standard) leagues, catches earn nothing on their own. This one rule can change which players and positions are most valuable, so every analysis here is run under both formats.
- **Points per game:** The average number of fantasy points a player scores per game played. It is the main measure of player performance in this analysis.
- **Replacement level:** The score of the best player still available once every team has filled its starting lineup. It shows how much a top player is worth compared with an easily found alternative.

**Motivation**
The motivation for us to work on this project is we are all sports fanatics.  Further, the introduction of Fantasy Foodball allows us to combine our passions of football with analytics and data science.  we have discussed potentially working in this industry and having hand on experience with something that data scientists in that industry would perform day to day gives us insight as to what it might be like to work in that industry.  Further, if we are able to continue this project, we could potentially create a recommender system type product that could have real monetary value.

**Data**

The analysis combines NFL and college player statistics. The NFL data (sourced through the `nflreadpy` package) has one row per player per week for 2018–2025. The college data is summarized by season. Because the two sources are structured differently, the analysis focuses on NFL players who return season after season.

**Topics covered**

1. **Drivers of fantasy performance.** Which statistics are most closely tied to scoring across all offensive positions, and which positions produce them? (Key Finding #1)
2. **Position-specific drivers.** How do scoring patterns differ by position and scoring format, and do they hold from season to season? (Key Finding #2)
3. **Positional draft strategy.** In a standard 12-team league, which positions should be drafted first in each scoring format? (Key Finding #3)
4. **Player selection by position.** For each position, which statistics identify strong players, and does opportunity (how often a player gets the ball) or efficiency (how well they use it) better predict next season's production?
5. **Summary and recommendations.** What matters most, what is reliable, and what are the limitations?

The goal is a strategic framework for drafting: which positions to prioritize and which general traits to look for. It is not a list of players to pick.

## Data Sources

### nflreadpy
  A collection of NFL datasets from various public sources.  This includes play by play data, player season stats, game schedules, team rosters, injury statues, as well as fantasy data and points.  It acts as a wrapper over these datasources: <br>
- nflverse-data: https://github.com/nflverse/nflverse-data <br>
- Dynasty process: https://github.com/dynastyprocess/data <br>
- Ffopportunity: https://github.com/ffverse/ffopportunity <br>

One season of player stats data has 18,643 records and 150 columns.  We used data for NFL seasons between 2018-2025 and the total size of the nflverse data we used from nflreadpy was 151,675 rows and 150 columns.  This data was served in polars, which we converted into pandas. 

**Significant Columns**
- player_display_name (which we later normalized to player)
- passing_epa (which was important in our QB efficiency analysis)
- target_share (which was important in our WR and TE analysis)

### CollegeFootballData API
This is college football data for college football players by season.  It also has data on the NFL draft in terms of when/if the player was selected, the year, the team and other details.  We collected but ultimately did not use the draft data in our analysis.  On the stats front, we ingested data for two years, with 2024 having 135,294 rows and 2025 having 141627 rows.  The reason for the high number of rows is because each row was one player and one stat.  As you can imagine, there are a large number of individual stats per player (for example a quarterback will have them on pass attempts, completions, interceptions, etc) this is what drove the large amount of records.  To touch lightly on the data processing here, we performed a pivot on these to combine all of these stats into one record per player and this dropped the total records down to slightly more than 15,000 records.  

**Significant Columns**:
- player
- position
- season <br>
Important because this because the basis of our join logic with nflreadpy <br>
The STAT column was also important as it had all the categories we used for statistics when we joined with the nflreadpy data

**Base URL**: https://api.collegefootballdata.com <br>
**Routes Used**: 
- /draft/picks (for draft data)
- /stats/player/season (for season data)


For this project, we used two primary data sources, nflverse through the python nflreadpy package and the CollegeFootballData API via API key.  The nflverse dataset provides player statistics at the week level, which we aggregated to the season level for analysis.  This dataset has one row per player per week for 2018-2025.  The CollegeFootballData API provides college football data at the season level, which we normalized and joined to the NFL data via a join key of position-player-season (note this was a concat since the records are distinct as no one, at least currently. can play in the NFL and college for the same season).  We did the normalizations via mappings files in the mappings directory that are used by data processing utility functions in the src/data_processing/utils_data_cleansing.py file.  Because the two sources differ in grain, the analysis focuses on returning NFL players and measures efficiency in fantasy points per game. Every analysis is run under both PPR and non-PPR scoring, since the one-point-per-reception rule changes which players and positions are most valuable.  We also applied minimum thresholds on things like passing attempts, rush attempts, and receiving targets that are in our config file to filter out potential noise in the data due to low player samples.

## Data Manipulation
For this project, we sought to use and combine two data sources, the nflverse data provided via nflreadpy and data from CollegeFootballData API.  The nflverse data through nflreadpy was provided in polars, which we converted to a pandas dataframe.  This data was provided at the week level, where each row represented a players stats for that week (assuming they played a game).  We used a mapping file to standardize some of the column names (across this dataset and the CollegeFootballData dataset).  Some of the column mappings we applied were player_display_name to player for the nflverse data and a number of coluumn renames to the CollegeFootballData, such as INT to passing_interceptions to standardize on column names between datasets.  The full details of the column changes for CollegeFootballData can be found here: mappings/college_football_stats_mapping.csv.  

The ingestion of the CollegeFootballData was via API, where an API key was stored in an environments file (which for best security practices, we did not commit to the repo and kept only on our developer laptops).  This data was in JSON which we transformed into pandas dataframes and later persisted to disk as csvs.  This persistance was to not rely on the API for recreating the project (as this would mean committing the API key to the repo itself, which is a bad security practice).  This data was served at the player level for a season and later we will describe the difficulties of dealing with data at two different grains.  

To join the dataset, we concatenated the two dataframes on a position-player-season key.  We concatenated instead of merged because, since these two datasets are entirely distinct (that is, as stated above, a player cannot play in both the NFL and college in the same season), there would not be overlap.  The combined data helped allow us to analyze players from both the nfl and college on similar statistics (which as stated above, we also normalized via the mappings file).  We also added a data_source column so we could see, from a lineage perspective, whether the row originated in nflverse or from the college dataset.  

The college football data did not provide data at the game/week level like nflreadpy so values of things like week, game_id, etc were not populated when the joined the datasets.  Since fantasy points per game require a games played denominator, this was foregone as well for college players.  We also didn't want to state that college players had earned fantasy points, when fantasy points are something that can only be achieved by NFL players, so all the fantasy point calculations were foregone for college players.  For purposes of analysis and not skewing some statistics, we also set minumum numbers for several positions, like passing attempts, rush attempts, targets, in a global configuration file here: config/config.toml where any players who did not meet this minum threshold were filtered from the dataframe and not included in the analysis or visualizations.  

The largest challenge we faced, from a data preparation perspective, for this project was, the grains of the nflreadpy and CollegeFootballData datasets were at different grains, with nflreadpy (nflreadverse) at the weekly level and CollegeFootballData at the season level, as stated above.  To resolve this, we aggregated the nfl data via group by on 'player', 'position', 'season', 'data_source' columns, which we stored as a global variable in the same global config file mentioned before.  The choice to store these variables in a config file allowed us to make changes to them in a file outside of the notebook, which would then be applied at all places the variables existed in the notebook, without having to carve through the code to make these changes.  We felt this was a more appropriate production implementation as it clearly separates code and configuration.  For the aggregation aspects of the group by, we summed various columns such as pass attempts, touchdowns, rush attempts, rushing touchdowns, targets, receptions and others which we applied to position specific dataframes.  We also calucalted various averages, such as passing and rushing yards per game and later used severals of these calculated fields in our analysis, to help us answer for each postion, which of these columns/features led to increases or decreses in fantasy points.  The output of this provided a clear playing field (football joke) for us to evenly evaluate pro and college players.


