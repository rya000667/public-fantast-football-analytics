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
CONFIG_PATH = PROJECT_ROOT / 'config' / 'config.toml'

# Adding consistent colors to use for each posistion in visualizations
POSITION_COLORS = {'QB': '#2ca02c', 'RB': '#d62728', 'WR': '#1f77b4', 'TE': '#ff7f0e'}
POSITION_COLOR_SCALE = alt.Scale(domain=list(POSITION_COLORS), range=list(POSITION_COLORS.values()))


with CONFIG_PATH.open('rb') as f:
    config = tomllib.load(f)


"""
Global Dashboard Filters
"""
season_filter = alt.param(
    name = 'selected_season',
    value = 2024,
    bind = alt.binding_select(
        options = config['GLOBAL_SEASONS_LIST'],
        name = 'Season'
    )
)

"""
QB Functions
"""

def qb_chart_top_fantasy_scorers(df, n = 15):
    """Bar chart: top N QBs by total fantasy points (optionally filtered to a season)."""

    title = f"Top {n} QBs by Fantasy Points"
    
    return (
        alt.Chart(df, title=title)
        .transform_filter(alt.datum.season == season_filter)
        .transform_window(
            rank = "rank()",
            sort = [alt.SortField("fantasy_points", order="descending")]
        )
        .transform_filter(alt.datum.rank <= n)
        .mark_bar(color="#2ca02c")
        .encode(
            x=alt.X("fantasy_points:Q", title="Fantasy Points"),
            y=alt.Y("player:N", sort="-x", title=None),
            tooltip=["player", "season", "attempts", "passing_tds", "fantasy_points"],
        ).add_params(season_filter)
        .properties(width=600, height=alt.Step(20))
    )


def qb_chart_efficiency(df):
    """Scatter: CPOE vs passing EPA, sized by attempts, colored by INTs."""
    return (
        alt.Chart(df, title="Accuracy Over Expected vs. EPA")
        .mark_circle(opacity=0.75)
        .encode(
            x=alt.X("passing_cpoe:Q", title="Completion % Over Expected"),
            y=alt.Y("passing_epa:Q", title="Passing EPA"),
            size=alt.Size("attempts:Q", title="Attempts"),
            color=alt.Color("passing_interceptions:Q", title="INTs", scale=alt.Scale(scheme="reds")),
            tooltip=["player", "season", "passing_cpoe", "passing_epa", "passing_interceptions", "attempts"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_efficiency")
    )


def qb_chart_dual_threat(df):
    """Scatter: passing yards vs rushing yards, sized by fantasy points."""
    return (
        alt.Chart(df, title="Dual-Threat Profile: Passing vs. Rushing")
        .mark_circle(opacity=0.75, color="#9467bd")
        .encode(
            x=alt.X("passing_yards:Q", title="Passing Yards"),
            y=alt.Y("rushing_yards:Q", title="Rushing Yards"),
            size=alt.Size("fantasy_points:Q", title="Fantasy Points"),
            tooltip=["player", "season", "passing_yards", "rushing_yards", "rushing_tds", "fantasy_points"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_dual_threat")
    )


def qb_chart_season_trend(df, players = None):
    """Line chart: avg fantasy points/game across seasons for selected players (or all)."""
    data = df if not players else df[df["player"].isin(players)]
    return (
        alt.Chart(data, title="Avg Fantasy Points per Game by Season")
        .mark_line(point=True)
        .encode(
            x=alt.X("season:O", title="Season"),
            y=alt.Y("avg_fantasy_points:Q", title="Avg Fantasy Pts / Game"),
            color=alt.Color("player:N", title="Player"),
            tooltip=["player", "season", "avg_fantasy_points", "passing_tds", "passing_interceptions"],
        )
        .properties(width=600, height=400)
    )


def qb_chart_sack_risk(df):
    """Scatter: attempts vs sacks suffered, colored by EPA, to flag pressure-prone QBs."""
    return (
        alt.Chart(df, title="Pass Attempts vs. Sacks Taken")
        .mark_circle(opacity=0.75, size=90)
        .encode(
            x=alt.X("attempts:Q", title="Pass Attempts"),
            y=alt.Y("sacks_suffered:Q", title="Sacks Suffered"),
            color=alt.Color("passing_epa:Q", title="Passing EPA", scale=alt.Scale(scheme="redblue", domainMid=0)),
            tooltip=["player", "season", "attempts", "sacks_suffered", "sack_yards_lost", "passing_epa"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )


def qb_chart_td_int_ratio(df):
    """Scatter: passing TDs vs INTs, one dot per player-season."""
    return (
        alt.Chart(df, title="TD-to-INT Profile")
        .mark_circle(opacity=0.75, size=90, color="#ff7f0e")
        .encode(
            x=alt.X("passing_interceptions:Q", title="Interceptions"),
            y=alt.Y("passing_tds:Q", title="Passing TDs"),
            tooltip=["player", "season", "passing_tds", "passing_interceptions", "completion_percentage"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )

"""
RB Functions
"""

def rb_chart_top_rushers(df, n = 15):
    """Bar chart: top N RBs by rushing yards (optionally filtered to a season)."""

    title = f"Top {n} RBs by Rushing Yards"

    return (
        alt.Chart(df, title=title)
        .transform_filter(alt.datum.season == season_filter)
        .transform_window(
            rank = "rank()",
            sort = [alt.SortField("fantasy_points", order="descending")]
        )
        .transform_filter(alt.datum.rank <= n)
        .mark_bar(color="#1f77b4")
        .encode(
            x=alt.X("rushing_yards:Q", title="Rushing Yards"),
            y=alt.Y("player:N", sort="-x", title=None),
            tooltip=["player", "season", "carries", "rushing_yards", "rushing_tds"],
        ).add_params(season_filter)
        .properties(width=600, height=alt.Step(20))
    )


def rb_chart_volume_vs_efficiency(df):
    """Scatter: carries vs yards/carry, sized by TDs, colored by EPA."""
    return (
        alt.Chart(df, title="Workload vs. Efficiency")
        .mark_circle(opacity=0.75)
        .encode(
            x=alt.X("carries:Q", title="Carries"),
            y=alt.Y("rush_yards_per_carry:Q", title="Yards per Carry"),
            size=alt.Size("rushing_tds:Q", title="Rushing TDs"),
            color=alt.Color("rushing_epa:Q", title="Rushing EPA", scale=alt.Scale(scheme="redblue", domainMid=0)),
            tooltip=["player", "season", "carries", "rush_yards_per_carry", "rushing_tds", "rushing_epa"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_efficiency")
    )


def rb_chart_receiving_involvement(df: pd.DataFrame):
    """Scatter: target share vs receiving yards, colored by RACR."""
    return (
        alt.Chart(df, title="Receiving Involvement")
        .mark_circle(opacity=0.75, size=90)
        .encode(
            x=alt.X("target_share:Q", title="Target Share", axis=alt.Axis(format="%")),
            y=alt.Y("receiving_yards:Q", title="Receiving Yards"),
            color=alt.Color("racr:Q", title="RACR", scale=alt.Scale(scheme="viridis")),
            tooltip=["player", "season", "targets", "receptions", "receiving_yards", "target_share", "racr"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_receiving")
    )


def rb_chart_player_trajectory(df, players = None):
    """Line chart: rush yards/game across seasons for selected players (or all)."""
    data = df if not players else df[df["player"].isin(players)]
    return (
        alt.Chart(data, title="Rush Yards per Game by Season")
        .mark_line(point=True)
        .encode(
            x=alt.X("season:O", title="Season"),
            y=alt.Y("rush_yards_per_game:Q", title="Rush Yds / Game"),
            color=alt.Color("player:N", title="Player"),
            tooltip=["player:N", "season", "rush_yards_per_game", "carries", "rushing_tds"],
        )
        .properties(width=600, height=400)
    )


def rb_chart_fumble_risk(df):
    """Scatter: touches vs fumbles lost, to flag ball-security risk."""
    data = df.copy()
    data["touches"] = data["carries"] + data["receptions"]
    data["fumbles_lost_total"] = data["rushing_fumbles_lost"] + data["receiving_fumbles_lost"]
    return (
        alt.Chart(data, title="Touches vs. Fumbles Lost")
        .mark_circle(opacity=0.7, size=90, color="#d62728")
        .encode(
            x=alt.X("touches:Q", title="Total Touches"),
            y=alt.Y("fumbles_lost_total:Q", title="Fumbles Lost"),
            tooltip=["player", "season", "touches", "fumbles_lost_total"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )


"""
WR Functions
"""
WR_COLOR = "#1f77b4"
def wr_chart_top_fantasy_scorers(df: pd.DataFrame, n: int = 15) -> alt.Chart:
    """Bar chart: top N WRs by total fantasy points."""

    title = f"Top {n} WRs by Fantasy Points"
    return (
        alt.Chart(df, title=title)
        .transform_filter(alt.datum.season == season_filter)
        .transform_window(
            rank = "rank()",
            sort = [alt.SortField("fantasy_points", order="descending")]
        )
        .transform_filter(alt.datum.rank <= n)
        .mark_bar(color=WR_COLOR)
        .encode(
            x=alt.X("fantasy_points:Q", title="Fantasy Points"),
            y=alt.Y("player:N", sort="-x", title=None),
            tooltip=["player", "season", "receptions", "receiving_yards",
                     "receiving_tds", "fantasy_points"],
        ).add_params(season_filter)
        .properties(width=600, height=alt.Step(20))
    )


def wr_chart_season_trend(df: pd.DataFrame, players: list[str] | None = None) -> alt.Chart:
    """Line chart: avg fantasy points/game across seasons per player."""
    data = df if not players else df[df["player"].isin(players)]
    return (
        alt.Chart(data, title="Avg Fantasy Points per Game by Season")
        .mark_line(point=True)
        .encode(
            x=alt.X("season:O", title="Season"),
            y=alt.Y("avg_fantasy_points:Q", title="Avg Fantasy Pts / Game"),
            color=alt.Color("player:N", title="Player"),
            tooltip=["player", "season", "avg_fantasy_points", "receiving_yards"],
        )
        .properties(width=600, height=400)
    )


def wr_chart_usage_vs_production(df: pd.DataFrame) -> alt.Chart:
    """Scatter: target share vs receiving yards, sized by TDs."""
    return (
        alt.Chart(df, title="Target Share vs. Receiving Yards")
        .mark_circle(opacity=0.7, color=WR_COLOR)
        .encode(
            x=alt.X("target_share:Q", title="Target Share", axis=alt.Axis(format="%")),
            y=alt.Y("receiving_yards:Q", title="Receiving Yards"),
            size=alt.Size("receiving_tds:Q", title="Receiving TDs"),
            tooltip=["player", "season", "target_share", "receiving_yards", "receiving_tds"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_usage")
    )


def wr_chart_air_yards_efficiency(df: pd.DataFrame) -> alt.Chart:
    """Scatter: air yards share vs target share, colored by RACR."""
    return (
        alt.Chart(df, title="Air Yards Share vs. Target Share (color = RACR)")
        .mark_circle(opacity=0.75, size=80)
        .encode(
            x=alt.X("air_yards_share:Q", title="Air Yards Share", axis=alt.Axis(format="%")),
            y=alt.Y("target_share:Q", title="Target Share", axis=alt.Axis(format="%")),
            color=alt.Color("racr:Q", title="RACR", scale=alt.Scale(scheme="viridis")),
            tooltip=["player", "season", "air_yards_share", "target_share", "racr"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_air")
    )


def wr_chart_explosiveness(df: pd.DataFrame) -> alt.Chart:
    """Scatter: yards/catch vs 20+ yard receptions."""
    return (
        alt.Chart(df, title="Big-Play Ability")
        .mark_circle(opacity=0.7, size=80, color=WR_COLOR)
        .encode(
            x=alt.X("rec_yards_per_catch:Q", title="Yards per Catch"),
            y=alt.Y("receiving_20:Q", title="20+ Yard Receptions"),
            tooltip=["player", "season", "rec_yards_per_catch", "receiving_20", "receiving_40"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )


def wr_chart_fantasy_distribution(df: pd.DataFrame) -> alt.Chart:
    """Histogram: distribution of avg fantasy points per game."""
    return (
        alt.Chart(df, title="Distribution of Avg Fantasy Points per Game")
        .mark_bar(color=WR_COLOR)
        .encode(
            x=alt.X("avg_fantasy_points:Q", bin=alt.Bin(maxbins=20), title="Avg Fantasy Pts / Game"),
            y=alt.Y("count()", title="Player-Seasons"),
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )


"""
TE Functions
"""
TE_COLOR = "#ff7f0e"
def te_chart_top_fantasy_scorers(df: pd.DataFrame, n: int = 15) -> alt.Chart:
    """Bar chart: top N TEs by total fantasy points."""

    title = f"Top {n} TEs by Fantasy Points"

    return (
        alt.Chart(df, title=title)
        .transform_filter(alt.datum.season == season_filter)
        .transform_window(
            rank = "rank()",
            sort = [alt.SortField("fantasy_points", order="descending")]
        )
        .transform_filter(alt.datum.rank <= n)
        .mark_bar(color=TE_COLOR)
        .encode(
            x=alt.X("fantasy_points:Q", title="Fantasy Points"),
            y=alt.Y("player:N", sort="-x", title=None),
            tooltip=["player", "season", "receptions", "receiving_yards",
                     "receiving_tds", "fantasy_points"],
        ).add_params(season_filter)
        .properties(width=600, height=alt.Step(20))
    )


def te_chart_season_trend(df: pd.DataFrame, players: list[str] | None = None) -> alt.Chart:
    """Line chart: avg fantasy points/game across seasons per player."""
    data = df if not players else df[df["player"].isin(players)]
    return (
        alt.Chart(data, title="Avg Fantasy Points per Game by Season")
        .mark_line(point=True)
        .encode(
            x=alt.X("season:O", title="Season"),
            y=alt.Y("avg_fantasy_points:Q", title="Avg Fantasy Pts / Game"),
            color=alt.Color("player:N", title="Player"),
            tooltip=["player", "season", "avg_fantasy_points", "receiving_yards"],
        )
        .properties(width=600, height=400)
    )


def te_chart_usage_vs_production(df: pd.DataFrame) -> alt.Chart:
    """Scatter: target share vs receiving yards, sized by TDs."""
    return (
        alt.Chart(df, title="Target Share vs. Receiving Yards")
        .mark_circle(opacity=0.7, color=TE_COLOR)
        .encode(
            x=alt.X("target_share:Q", title="Target Share", axis=alt.Axis(format="%")),
            y=alt.Y("receiving_yards:Q", title="Receiving Yards"),
            size=alt.Size("receiving_tds:Q", title="Receiving TDs"),
            tooltip=["player", "season", "target_share", "receiving_yards", "receiving_tds"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_usage")
    )


def te_chart_air_yards_efficiency(df: pd.DataFrame) -> alt.Chart:
    """Scatter: air yards share vs target share, colored by RACR."""
    return (
        alt.Chart(df, title="Air Yards Share vs. Target Share (color = RACR)")
        .mark_circle(opacity=0.75, size=80)
        .encode(
            x=alt.X("air_yards_share:Q", title="Air Yards Share", axis=alt.Axis(format="%")),
            y=alt.Y("target_share:Q", title="Target Share", axis=alt.Axis(format="%")),
            color=alt.Color("racr:Q", title="RACR", scale=alt.Scale(scheme="viridis")),
            tooltip=["player", "season", "air_yards_share", "target_share", "racr"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=400)
        .interactive("pan_zoom_air")
    )


def te_chart_explosiveness(df: pd.DataFrame) -> alt.Chart:
    """Scatter: yards/catch vs 10+ yard receptions."""
    return (
        alt.Chart(df, title="Big-Play Ability")
        .mark_circle(opacity=0.7, size=80, color=TE_COLOR)
        .encode(
            x=alt.X("rec_yards_per_catch:Q", title="Yards per Catch"),
            y=alt.Y("receiving_10:Q", title="10+ Yard Receptions"),
            tooltip=["player", "season", "rec_yards_per_catch", "receiving_10", "receiving_40"],
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )


def te_chart_fantasy_distribution(df: pd.DataFrame) -> alt.Chart:
    """Histogram: distribution of avg fantasy points per game."""
    return (
        alt.Chart(df, title="Distribution of Avg Fantasy Points per Game")
        .mark_bar(color=TE_COLOR)
        .encode(
            x=alt.X("avg_fantasy_points:Q", bin=alt.Bin(maxbins=20), title="Avg Fantasy Pts / Game"),
            y=alt.Y("count()", title="Player-Seasons"),
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )



def chart_fantasy_distribution(df: pd.DataFrame) -> alt.Chart:
    """Histogram: distribution of avg fantasy points per game."""
    return (
        alt.Chart(df, title="Distribution of Avg Fantasy Points per Game")
        .mark_bar(color=TE_COLOR)
        .encode(
            x=alt.X("avg_fantasy_points:Q", bin=alt.Bin(maxbins=20), title="Avg Fantasy Pts / Game"),
            y=alt.Y("count()", title="Player-Seasons"),
        ).add_params(season_filter)
         .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )

## All-In Functions

def targeted_heatmap(df, targets, title, exclude=(), min_corr=0.1):
    """Correlation of every numeric column with each target, shown side by side."""
    num = df.select_dtypes(include='number')

    data = (
        num.drop(columns=[*targets, *exclude], errors='ignore')
        .apply(lambda col: num[targets].corrwith(col))   # rows: stats, columns: targets
        .T
        .dropna(how='all')
    )

    # keep stats where at least one target has |r| >= min_corr
    data = data[(data.abs() >= min_corr).any(axis=1)]

    data = (
        data.rename_axis('stat')
        .reset_index()
        .melt(id_vars='stat', var_name='target', value_name='correlation')
    )

    # order stats by correlation with the first target, strongest first
    order = (
        data[data['target'] == targets[0]]
        .sort_values('correlation', ascending=False)['stat']
        .tolist()
    )

    return alt.Chart(data, title=title).mark_rect().encode(
        x=alt.X('target:N', title=None, sort=targets),
        y=alt.Y('stat:N', title=None, sort=order),
        color=alt.Color('correlation:Q', scale=alt.Scale(scheme='redblue', domain=[-1, 1], reverse=True)),
        tooltip=['stat', 'target', alt.Tooltip('correlation:Q', format='.2f')],
    ).properties(width=80 * len(targets), height=600)



def corr_bar_chart(df, target, title, exclude=(), min_corr=0.3):
    num = df.select_dtypes(include='number')
    data = (
        num.drop(columns=[target, *exclude], errors='ignore')
        .corrwith(num[target])
        .dropna()
        .rename('correlation')
        .rename_axis('stat')
        .reset_index()
    )
    data = data[data['correlation'].abs() >= min_corr]

    bars = alt.Chart(data, title=title).mark_bar().encode(
        x=alt.X('correlation:Q', scale=alt.Scale(domain=[-1, 1]), title='Correlation (r)'),
        y=alt.Y('stat:N', sort='-x', title=None),
        color=alt.condition('datum.correlation > 0', alt.value('#2b6cb0'), alt.value('#c53030')),
        tooltip=['stat', alt.Tooltip('correlation:Q', format='.2f')],
    )
    labels = bars.mark_text(align='left', dx=3).encode(
        text=alt.Text('correlation:Q', format='.2f'), color=alt.value('black')
    )
    return (bars + labels).properties(width=400, height=alt.Step(18))



def chart_fantasy_distribution(df: pd.DataFrame, position: str | None = None,
                               value_col: str = 'avg_fantasy_points', maxbins: int = 20) -> alt.Chart:
    """Histogram: distribution of avg fantasy points per game for one position, or all positions stacked if None."""
    data = df[df['position'].isin(POSITION_COLORS)] if position is None else df[df['position'] == position]
    label = position or 'All Positions'

    return (
        alt.Chart(data, title=f"Distribution of Avg Fantasy Points per Game: {label}")
        .mark_bar()
        .encode(
            x=alt.X(f"{value_col}:Q", bin=alt.Bin(maxbins=maxbins), title="Avg Fantasy Pts / Game"),
            y=alt.Y("count()", title="Player-Seasons"),
            color=alt.Color('position:N', scale=POSITION_COLOR_SCALE, sort=list(POSITION_COLORS),
                            legend=None if position else alt.Legend(title='Position')),
            order=alt.Order('position_order:Q'),
            tooltip=['position', alt.Tooltip('count()', title='Player-Seasons')],
        )
        .transform_calculate(position_order=f"indexof({list(POSITION_COLORS)}, datum.position)")
        .add_params(season_filter)
        .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=350)
    )


def chart_fantasy_distribution_by_position(df: pd.DataFrame, positions: list[str] = list(POSITION_COLORS),
                                           value_col: str = 'avg_fantasy_points', maxbins: int = 20) -> alt.FacetChart:
    """Histograms of avg fantasy points per game, one panel per position, on a shared x-axis."""
    return (
        alt.Chart(df[df['position'].isin(positions)])
        .mark_bar()
        .encode(
            x=alt.X(f"{value_col}:Q", bin=alt.Bin(maxbins=maxbins), title="Avg Fantasy Pts / Game"),
            y=alt.Y("count()", title="Player-Seasons"),
            color=alt.Color('position:N', scale=POSITION_COLOR_SCALE, legend=None),
            tooltip=['position', alt.Tooltip('count()', title='Player-Seasons')],
        )
        .add_params(season_filter)
        .transform_filter(alt.datum.season == season_filter)
        .properties(width=600, height=120)
        .facet(row=alt.Row('position:N', sort=positions, title=None))
        .resolve_scale(y='independent')
        .properties(title="Distribution of Avg Fantasy Points per Game by Position")
    )




"""
Dashboard Functions
"""
def build_qb_dashboard(df,):
    row1 = alt.hconcat(qb_chart_top_fantasy_scorers(df), qb_chart_season_trend(df))
    row2 = alt.hconcat(qb_chart_efficiency(df), qb_chart_dual_threat(df))
    row3 = alt.hconcat(qb_chart_sack_risk(df), qb_chart_td_int_ratio(df))
    return alt.vconcat(row1, row2, row3).properties(
        title=alt.TitleParams("QB Fantasy Football Dashboard", fontSize=20)
    )

def build_rb_dashboard(df):
    row1 = alt.hconcat(rb_chart_volume_vs_efficiency(df), rb_chart_receiving_involvement(df))
    row2 = alt.hconcat(rb_chart_top_rushers(df), rb_chart_player_trajectory(df))
    row3 = rb_chart_fumble_risk(df)
    return alt.vconcat(row1, row2, row3).properties(
        title=alt.TitleParams("RB Fantasy Football Dashboard", fontSize=20)
    )

def build_wr_dashboard(df: pd.DataFrame) -> alt.VConcatChart:
    row1 = alt.hconcat(wr_chart_top_fantasy_scorers(df), wr_chart_season_trend(df))
    row2 = alt.hconcat(wr_chart_usage_vs_production(df), wr_chart_air_yards_efficiency(df))
    row3 = alt.hconcat(wr_chart_explosiveness(df), wr_chart_fantasy_distribution(df))
    return alt.vconcat(row1, row2, row3).properties(
        title=alt.TitleParams("WR Fantasy Football Dashboard", fontSize=20)
    )

def build_te_dashboard(df: pd.DataFrame) -> alt.VConcatChart:
    row1 = alt.hconcat(te_chart_top_fantasy_scorers(df), te_chart_season_trend(df))
    row2 = alt.hconcat(te_chart_usage_vs_production(df), te_chart_air_yards_efficiency(df))
    row3 = alt.hconcat(te_chart_explosiveness(df), te_chart_fantasy_distribution(df))
    return alt.vconcat(row1, row2, row3).properties(
        title=alt.TitleParams("TE Fantasy Football Dashboard", fontSize=20)
    )


