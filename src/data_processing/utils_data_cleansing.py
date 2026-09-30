"""
Module for data cleansing and preprocessing functions
"""
from collections. abc import Mapping
import pandas as pd
from pathlib import Path
import json

def clean_transform_positions(df:pd.DataFrame, position_map: Mapping[str,str], column:str) -> pd.DataFrame:
    """
    Standardize various Quarterback, qb, QB to be QB, Running Back to RB, etc.  Leverage position_map.json to do this
    """
    df[column] = df[column].str.lower().map(position_map)
    return df


def load_college_data(relative_path:str='src/data_ingestion/college_data') ->dict[str, pd.DataFrame]:
    """
    Load college data from JSON files and return a dictionary of DataFrames
    """
    BASE_DIR = Path.cwd()
    DATA_DIR = BASE_DIR / relative_path

    # Hold DataFrames
    dfs = {}

    # Read in all JSON files in the data directory and normalize them into DataFrames
    for item in DATA_DIR.iterdir():
        if item.is_file():
            with open(item, encoding="utf-8") as f:
                dfs[item.stem] = pd.json_normalize(json.load(f), sep="_")
            print(f"Loaded {item.stem} into DataFrame with shape {dfs[item.stem].shape}")

    return dfs


def create_college_stats_dataframe(dataframe_dict: dict[str, pd.DataFrame]) ->pd.DataFrame:
    """
    Combine the dict of dataframes into one dataframe
    """
    stat_categories = set(dataframe_dict['2024_stats'].category.unique()) - set(dataframe_dict['2025_stats'].category.unique())

    if len(stat_categories) > 0:
        print(f"Stat categories in 2024 but not in 2025: {stat_categories}")
    else:
        print("All stat categories are the same between 2024 and 2025 stats.")
        stat_categories = set(dataframe_dict['2025_stats'].category.unique()) & set(dataframe_dict['2024_stats'].category.unique())
        print(f"Stat categories in both 2024 and 2025: {stat_categories}")
    
    all_stats =  pd.concat([dataframe_dict["2024_stats"], dataframe_dict["2025_stats"]], ignore_index=True)

    return all_stats
    
def process_college_features(college_df:pd.DataFrame, features_list:list['str']=['receiving', 'passing', 'rushing', 'fumbles', 'kicking']) -> pd.DataFrame:
    """
    """
    all_stats_filtered = college_df[college_df['category'].isin(features_list)]
    print(f"Features Removed: {set(college_df['category'].unique()) - set(all_stats_filtered['category'].unique())}")

    return all_stats_filtered


def create_college_draft_dataframe(dataframe_dict:dict[str, pd.DataFrame])-> pd.DataFrame:
    """
    """
    draft_features = set(dataframe_dict['2025_draft'].columns) - set(dataframe_dict['2026_draft'].columns)
    if len(draft_features) > 0:
        print(f"Draft features in 2025 but not in 2026: {draft_features}")
    else: 
        print("All draft features are the same between 2025 and 2026 stats.")
        draft_features = set(dataframe_dict['2025_draft'].columns) & set(dataframe_dict['2026_draft'].columns)
        print(f"Draft features in both 2025 and 2026: {draft_features}")

    all_draft = pd.concat([dataframe_dict["2025_draft"], dataframe_dict["2026_draft"]], ignore_index=True)

    # View Features in the all_draft DataFrame
    print(all_draft.columns)

    return all_draft

def process_college_draft_data(draft_df:pd.DataFrame, features_list:list['str']=['collegeAthleteId', 'nflAthleteId', 'collegeId', 'collegeTeam',
       'collegeConference', 'nflTeamId', 'nflTeam', 'year', 'overall', 'round',
       'pick', 'name', 'position', 'height', 'weight', 'preDraftRanking',
       'preDraftPositionRanking', 'preDraftGrade', 'hometownInfo_city',
       'hometownInfo_state']) -> pd.DataFrame:
    """
    """
    all_draft_filtered = draft_df[features_list]
    print(f"Features Removed: {set(draft_df.columns) - set(all_draft_filtered.columns)}")

    return all_draft_filtered


def aggregate_stats_df(stats_df:pd.DataFrame) -> pd.DataFrame:
    """
    Combine the college stats and draft dataframes on the specified column
    """
    all_stats_filtered_pivot = stats_df.pivot(index=['season','playerId','player','position','team','conference','category'], columns='statType', values='stat').reset_index()
    all_stats_filtered_pivot.head()

    return all_stats_filtered_pivot