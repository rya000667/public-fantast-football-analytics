from dotenv import load_dotenv
import pandas as pd
import nflreadpy as nfl
import altair as alt

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio

from src.data_processing import utils_data_cleansing as utils
import tomllib
from pathlib import Path

# Resolve from this file's location so imports work from any working directory
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = PROJECT_ROOT / "config" / "config.toml"

with CONFIG_PATH.open("rb") as f:
    config = tomllib.load(f)


# Global constants for offensive positions and aggregation functions
offensive_aggregates = {
    # passing
    "completions": "sum",
    "attempts": "sum",
    "passing_yards": "sum",
    "passing_tds": "sum",
    "passing_interceptions": "sum",
    "passing_2pt_conversions": "sum",
    "sacks_suffered": "sum",
    "sack_yards_lost": "sum",
    "sack_fumbles": "sum",
    "sack_fumbles_lost": "sum",
    "passing_air_yards": "sum",
    "passing_yards_after_catch": "sum",
    "passing_first_downs": "sum",
    "passing_epa": "sum",
    "passing_cpoe": "mean",
    "pacr": "mean",
    # rushing
    "carries": "sum",
    "rushing_yards": "sum",
    "rushing_tds": "sum",
    "rushing_fumbles": "sum",
    "rushing_fumbles_lost": "sum",
    "rushing_first_downs": "sum",
    "rushing_epa": "sum",
    "rushing_2pt_conversions": "sum",
    # receiving
    "receptions": "sum",
    "targets": "sum",
    "receiving_yards": "sum",
    "receiving_tds": "sum",
    "receiving_fumbles": "sum",
    "receiving_fumbles_lost": "sum",
    "receiving_air_yards": "sum",
    "receiving_yards_after_catch": "sum",
    "receiving_first_downs": "sum",
    "receiving_epa": "sum",
    "receiving_2pt_conversions": "sum",
    "racr": "mean",
    "target_share": "mean",
    "air_yards_share": "mean",
    # all
    "games_played_unit": "sum",
}

offensive_positions = ["QB", "RB", "WR", "TE"]


all_player_cols = [
    "player_id",
    "player_name",
    "player",
    "position",
    "position_group",
    #'headshot_url',
    "season",
    "week",
    "season_type",
    "game_id",
    "team",
    "opponent_team",
    #'data_source',
    #'games_played_unit'
]


# Data Manipulation Functions


def calculate_mean_passing_stats_by_year(
    df: pd.DataFrame, year: int
) -> tuple[float, float, float, float, float, float]:
    """ """
    # filter for specified year
    season_df = df[df["season"] == year]

    # get stats
    avg_total_games_played = season_df["total_games_played"].mean()
    avg_completions = season_df["completions"].mean()
    avg_passing_yards = season_df["passing_yards"].mean()
    avg_passing_tds = season_df["passing_tds"].mean()
    avg_passing_interceptions = season_df["passing_interceptions"].mean()
    avg_passing_yards_per_game = season_df["passing_yards_per_game"].mean()

    return (
        avg_total_games_played,
        avg_completions,
        avg_passing_yards,
        avg_passing_tds,
        avg_passing_interceptions,
        avg_passing_yards_per_game,
    )


def safe_div(num: pd.Series, den: pd.Series) -> pd.Series:
    """
    Divide two Series, returning NaN instead of inf where the denominator is 0
    """
    return num / den.where(den != 0)


def aggregate_offense_season(
    df: pd.DataFrame,
    groupby_cols: list[str],
    positions: list[str] = offensive_positions,
) -> pd.DataFrame:
    """
    Aggregate weekly offensive stats to one row per groupby_cols (e.g. player-season).
    Keeps only players with at least one pass attempt, carry, or target.
    """
    season_agg = (
        df[df["position"].isin(positions)]
        .groupby(groupby_cols)
        .agg(offensive_aggregates)
        .rename(columns={"games_played_unit": "total_games_played"})
        .reset_index()
    )

    active = (
        season_agg["attempts"] + season_agg["carries"] + season_agg["targets"]
    ) > 0
    return season_agg[active].copy()


def add_rate_stats(season_agg: pd.DataFrame) -> pd.DataFrame:
    """
    Add per-game and per-opportunity rate stats
    """
    g = season_agg["total_games_played"]
    season_agg["completion_pct"] = safe_div(
        season_agg["completions"], season_agg["attempts"]
    )
    season_agg["pass_yards_per_att"] = safe_div(
        season_agg["passing_yards"], season_agg["attempts"]
    )
    season_agg["pass_yards_per_game"] = safe_div(season_agg["passing_yards"], g)
    season_agg["rush_yards_per_carry"] = safe_div(
        season_agg["rushing_yards"], season_agg["carries"]
    )
    season_agg["rush_yards_per_game"] = safe_div(season_agg["rushing_yards"], g)
    season_agg["rec_yards_per_catch"] = safe_div(
        season_agg["receiving_yards"], season_agg["receptions"]
    )
    season_agg["rec_yards_per_game"] = safe_div(season_agg["receiving_yards"], g)
    season_agg["catch_rate"] = safe_div(season_agg["receptions"], season_agg["targets"])
    return season_agg


def add_fantasy_points(season_agg: pd.DataFrame, ppr: float = 0) -> pd.DataFrame:
    """
    Add total and per-game fantasy points.
    Standard scoring; ppr=1 for full PPR, 0.5 for half PPR.
    """
    season_agg["fantasy_points"] = (
        season_agg["passing_yards"] * 0.04
        + season_agg["passing_tds"] * 6
        - season_agg["passing_interceptions"] * 2
        + season_agg["rushing_yards"] * 0.1
        + season_agg["rushing_tds"] * 6
        + season_agg["receiving_yards"] * 0.1
        + season_agg["receiving_tds"] * 6
        + season_agg["receptions"] * ppr
        + (
            season_agg["passing_2pt_conversions"]
            + season_agg["rushing_2pt_conversions"]
            + season_agg["receiving_2pt_conversions"]
        )
        * 2
        - (
            season_agg["rushing_fumbles_lost"]
            + season_agg["receiving_fumbles_lost"]
            + season_agg["sack_fumbles_lost"]
        )
        * 2
    )
    season_agg["avg_fantasy_points"] = safe_div(
        season_agg["fantasy_points"], season_agg["total_games_played"]
    )
    return season_agg


def build_offense_season_agg(
    df: pd.DataFrame,
    groupby_cols: list[str],
    ppr: float = 0,
    positions: list[str] = offensive_positions,
) -> pd.DataFrame:
    """
    Full pipeline: aggregate to season level, add rate stats, add fantasy points
    """
    season_agg = aggregate_offense_season(df, groupby_cols, positions)
    season_agg = add_rate_stats(season_agg)
    return add_fantasy_points(season_agg, ppr)
