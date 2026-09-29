"""
Module for data cleansing and preprocessing functions
"""
from collections. abc import Mapping
import pandas as pd


def clean_transform_positions(df:pd.DataFrame, position_map: Mapping[str,str], column:str) -> pd.DataFrame:
    """
    Standardize various Quarterback, qb, QB to be QB, Running Back to RB, etc.  Leverage position_map.json to do this
    """
    pass
