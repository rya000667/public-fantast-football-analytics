# ChangeLog

## Features to Work (unreleased)
- Box plot
- Violin Plot
- Dendrogram
- Ethical Considerations for Selection Bias
- Ethical implications for gambling
- Multiple linear regression (low priority, achieve all others before touching)
- Clustering Analysis (low priority, achive all others before touching)

## Added
#### General
- Adjusted directory structure for ingestion and preprocessing modules
- Created utils_data_cleansing for merging across datasets and wraping preprocessing steps into functions
- Creation of Join Key across nflreadpy data and api.collegefootballdata (fullname - year - position looks hopeful)
- Normalization of columns between collegefootballdata and nflreadpy

#### nflreadpy Features
- Initial Ingestion of nflreadpy data
- Team and Player DataFrames
- Broke out useful columns by position
- Added additional QB statistics
- QB Aggregations for season data
- Descriptive Statistics for QB data
- QB Bar Chart with Statistics overlay
- Initial RB DataFrame
- Initial Receiver DataFrame
- Initial Defense DataFrame
- Correlation Heatmap
- Scatter Plot
- Histogram
- Line Graphs
- EDA of fantasy points data and later tie in to position players
- Continued EDA across position players (RB, Receivers, Defense, others can be added as needed)
- Added filters for season for all dashboards
- Fixed Top 15 fantasy players by position to leverage season filter

#### api.collegefootballdata Features
- api.collegefootballdata.com ingestion
- Backfilling for 2024, 2025 Season Stats
- Backfilling for 2025, 2026 Draft
- Data persistence for above to src/data_ingestion/college_data
- Processing to pandas DataFrame
- Inital Data Processing
- Feature Selection

#### api-sports Features
- api-sports ingestion





