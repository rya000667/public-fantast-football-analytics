import numpy as np
import pandas as pd
import altair as alt
import sys
import tomllib
from pathlib import Path

CONFIG_PATH = Path("config/config.toml")

with CONFIG_PATH.open("rb") as f:
    config = tomllib.load(f)
POSITION_COLORS = {"QB": "#2ca02c", "RB": "#d62728", "WR": "#1f77b4", "TE": "#ff7f0e"}
POSITION_COLOR_SCALE = alt.Scale(
    domain=list(POSITION_COLORS), range=list(POSITION_COLORS.values())
)

season_filter = alt.param(
    name="selected_season",
    value=2024,
    bind=alt.binding_select(options=config["GLOBAL_SEASONS_LIST"], name="Season"),
)
CORR_MIN_GAMES = 6  # drop player-seasons with fewer games than this
CORR_LAST_SEASON = 2025  # the current season is partial, so leave it out
# (column, minimum) a player-season needs to count; keeps tiny samples out
CORR_MIN_VOLUME = {
    "QB": ("attempts", 100),
    "RB": ("touches_raw", 40),  # carries + targets
    "WR": ("targets", 30),
    "TE": ("targets", 30),
}

# Stats that are literally terms in the scoring formula. Their correlation with
# points is close to automatic, so they are drawn in gray, not blue.
SCORING_COMPONENTS = {
    "Pass TDs per game",
    "Pass yards per game",
    "Rush TDs per game",
    "Rush yards per game",
    "Receptions per game",
    "Receiving TDs per game",
    "Receiving yards per game",
}

KIND_SCALE = alt.Scale(
    domain=["Underlying driver", "Scoring component", "Negative / none"],
    range=["#2a78d6", "#a8a79f", "#e34948"],
)
OPP_EFF_SCALE = alt.Scale(
    domain=["Opportunity", "Efficiency"], range=["#2a78d6", "#eb6834"]
)

# (opportunity stat, efficiency stat) used by the opportunity-vs-efficiency chart
OPP_EFF_SAME = {
    "QB": ("Pass attempts per game", "EPA per pass attempt"),
    "RB": ("Touches per game", "Yards per carry"),
    "WR": ("Targets per game", "Yards per target"),
    "TE": ("Targets per game", "Yards per target"),
}
# next-season check uses carries (not touches) for RBs
OPP_EFF_NEXT = {**OPP_EFF_SAME, "RB": ("Carries per game", "Yards per carry")}


# --- feature builders: points per game (ppg) plus per-game and rate stats ---
# Scoring matches the notebook: full PPR, 6-pt TDs, -2 per fumble / interception.
def _qb_features(d):
    g = d["total_games_played"]
    fp = (
        d["passing_yards"] * 0.04
        + d["passing_tds"] * 6
        + d["rushing_yards"] * 0.1
        + d["rushing_tds"] * 6
        + d["rushing_2pt_conversions"] * 2
        - d["sack_fumbles_lost"] * 2
        - d["passing_interceptions"] * 2
    )
    return pd.DataFrame(
        {
            "ppg": fp / g,
            "Pass TDs per game": d["passing_tds"] / g,
            "TD rate (per attempt)": d["passing_tds"] / d["attempts"],
            "EPA per pass attempt": d["passing_epa"] / d["attempts"],
            "Pass yards per game": d["passing_yards"] / g,
            "First downs per game": d["passing_first_downs"] / g,
            "Yards per attempt": d["passing_yards"] / d["attempts"],
            "CPOE": d["passing_cpoe"],
            "Pass attempts per game": d["attempts"] / g,
            "Completion %": d["completions"] / d["attempts"],
            "Rush attempts per game": d["carries"] / g,
            "Rush TDs per game": d["rushing_tds"] / g,
            "Rush yards per game": d["rushing_yards"] / g,
            "Air yards per attempt": d["passing_air_yards"] / d["attempts"],
            "Sacks per game": d["sacks_suffered"] / g,
            "Interception rate": d["passing_interceptions"] / d["attempts"],
        }
    )


def _rb_features(d):
    g = d["total_games_played"]
    fp = (
        d["rushing_yards"] * 0.1
        + d["receiving_yards"] * 0.1
        + d["receptions"]
        + (d["rushing_tds"] + d["receiving_tds"]) * 6
        + (d["rushing_2pt_conversions"] + d["receiving_2pt_conversions"]) * 2
        - (d["rushing_fumbles"] + d["receiving_fumbles"]) * 2
    )
    targets = d["targets"].replace(0, np.nan)
    return pd.DataFrame(
        {
            "ppg": fp / g,
            "Touches per game": (d["carries"] + d["receptions"]) / g,
            "Carries per game": d["carries"] / g,
            "Rush TDs per game": d["rushing_tds"] / g,
            "Receptions per game": d["receptions"] / g,
            "Rush first downs per game": d["rushing_first_downs"] / g,
            "Targets per game": d["targets"] / g,
            "Receiving TDs per game": d["receiving_tds"] / g,
            "Yards per target": d["receiving_yards"] / targets,
            "Receiving EPA": d["receiving_epa"],
            "Catch rate": d["receptions"] / targets,
            "Yards per carry": d["rushing_yards"] / d["carries"],
            "Rushing EPA": d["rushing_epa"],
        }
    )


def _receiver_features(d):
    """WR and TE share the same feature set."""
    g = d["total_games_played"]
    fp = (
        d["receiving_yards"] * 0.1
        + d["receptions"]
        + d["receiving_tds"] * 6
        + d["receiving_2pt_conversions"] * 2
        - d["receiving_fumbles"] * 2
    )
    recs = d["receptions"].replace(0, np.nan)
    return pd.DataFrame(
        {
            "ppg": fp / g,
            "Receiving yards per game": d["receiving_yards"] / g,
            "Receptions per game": d["receptions"] / g,
            "First downs per game": d["receiving_first_downs"] / g,
            "Targets per game": d["targets"] / g,
            "Receiving TDs per game": d["receiving_tds"] / g,
            "Receiving EPA": d["receiving_epa"],
            "YAC per game": d["receiving_yards_after_catch"] / g,
            "Air yards per game": d["receiving_air_yards"] / g,
            "Air yards share": d["air_yards_share"],
            "Yards per target": d["receiving_yards"] / d["targets"],
            "Catch rate": d["receptions"] / d["targets"],
            "Yards per reception": d["receiving_yards"] / recs,
            "YAC per reception": d["receiving_yards_after_catch"] / recs,
            "Avg depth of target": d["receiving_air_yards"] / d["targets"],
        }
    )


_FEATURE_BUILDERS = {
    "QB": _qb_features,
    "RB": _rb_features,
    "WR": _receiver_features,
    "TE": _receiver_features,
}


def corr_features(df: pd.DataFrame, position: str) -> pd.DataFrame:
    """One row per qualifying NFL player-season: player, season, ppg and the position's stats."""
    d = df.copy()
    if "data_source" in d.columns:
        d = d[d["data_source"] == "nflreadpy"]
    d = d[
        (d["season"] <= CORR_LAST_SEASON) & (d["total_games_played"] >= CORR_MIN_GAMES)
    ].copy()
    d["touches_raw"] = d["carries"] + d["targets"] if position == "RB" else np.nan
    col, minimum = CORR_MIN_VOLUME[position]
    d = d[d[col] >= minimum]
    feats = _FEATURE_BUILDERS[position](d)
    return pd.concat([d[["player", "season"]], feats], axis=1).reset_index(drop=True)


def driver_correlations(feats: pd.DataFrame) -> pd.DataFrame:
    """Correlation of every stat with ppg, tagged as driver / scoring component / negative."""
    stats = [c for c in feats.columns if c not in ("player", "season", "ppg")]
    out = (
        feats[stats]
        .corrwith(feats["ppg"])
        .dropna()
        .rename("correlation")
        .rename_axis("stat")
        .reset_index()
    )
    out["kind"] = [
        (
            "Scoring component"
            if s in SCORING_COMPONENTS
            else ("Negative / none" if r < 0.1 else "Underlying driver")
        )
        for s, r in zip(out["stat"], out["correlation"])
    ]
    return out


def opp_eff_table(feats: pd.DataFrame, position: str) -> pd.DataFrame:
    """Correlation of the opportunity and efficiency stats with ppg: same season and next season."""
    nxt = feats[["player", "season", "ppg"]].copy()
    nxt["season"] = nxt["season"] - 1
    merged = feats.merge(
        nxt.rename(columns={"ppg": "next_ppg"}), on=["player", "season"]
    )
    rows = []
    for when, spec, frame, target in (
        ("Same season", OPP_EFF_SAME[position], feats, "ppg"),
        ("Next season", OPP_EFF_NEXT[position], merged, "next_ppg"),
    ):
        for metric, stat in zip(("Opportunity", "Efficiency"), spec):
            rows.append(
                {
                    "when": when,
                    "metric": metric,
                    "stat": stat,
                    "correlation": frame[stat].corr(frame[target]),
                    "n": len(frame),
                }
            )
    return pd.DataFrame(rows)


def chart_driver_correlations(df: pd.DataFrame, position: str) -> alt.LayerChart:
    """Bars: correlation of each stat with fantasy points per game.
    Blue = underlying driver, gray = scoring component (mechanical), red = negative / none.
    """
    feats = corr_features(df, position)
    data = driver_correlations(feats)
    title = alt.TitleParams(
        f"{position}: What Correlates with Fantasy Points per Game",
        subtitle=f"{len(feats)} NFL player-seasons, {feats['season'].min()}-{feats['season'].max()}, "
        f"min {CORR_MIN_GAMES} games. Ignores the season filter.",
    )
    bars = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                "correlation:Q",
                title="Correlation (r)",
                scale=alt.Scale(domain=[-0.5, 1.15]),
            ),
            y=alt.Y(
                "stat:N",
                sort=alt.EncodingSortField("correlation", order="descending"),
                title=None,
                axis=alt.Axis(labelLimit=220),
            ),
            color=alt.Color(
                "kind:N",
                scale=KIND_SCALE,
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=["stat", "kind", alt.Tooltip("correlation:Q", format=".2f")],
        )
    )
    labels_pos = (
        bars.mark_text(align="left", dx=4)
        .encode(text=alt.Text("correlation:Q", format=".2f"), color=alt.value("black"))
        .transform_filter("datum.correlation >= 0")
    )
    labels_neg = (
        bars.mark_text(align="right", dx=-4)
        .encode(text=alt.Text("correlation:Q", format=".2f"), color=alt.value("black"))
        .transform_filter("datum.correlation < 0")
    )
    return alt.layer(bars, labels_pos, labels_neg).properties(
        title=title, width=450, height=alt.Step(20)
    )


def chart_opportunity_vs_efficiency(df: pd.DataFrame, position: str) -> alt.LayerChart:
    """Grouped bars: opportunity vs efficiency, correlated with this season's and next season's ppg."""
    t = opp_eff_table(corr_features(df, position), position)
    opp, eff = OPP_EFF_SAME[position]
    note = (
        ""
        if OPP_EFF_NEXT[position] == OPP_EFF_SAME[position]
        else " (next season uses carries per game)"
    )
    title = alt.TitleParams(
        f"{position}: Opportunity vs. Efficiency",
        subtitle=f"Opportunity = {opp}; efficiency = {eff}{note}",
    )
    lo = min(0.0, float(t["correlation"].min()) - 0.1)
    base = alt.Chart(t).encode(
        x=alt.X(
            "when:N",
            sort=["Same season", "Next season"],
            title=None,
            axis=alt.Axis(labelAngle=0),
        ),
        xOffset=alt.XOffset("metric:N", sort=["Opportunity", "Efficiency"]),
        y=alt.Y(
            "correlation:Q", title="Correlation (r)", scale=alt.Scale(domain=[lo, 1.05])
        ),
        color=alt.Color(
            "metric:N",
            scale=OPP_EFF_SCALE,
            legend=alt.Legend(title=None, orient="bottom"),
        ),
        tooltip=[
            "when",
            "metric",
            "stat",
            alt.Tooltip("correlation:Q", format=".2f"),
            alt.Tooltip("n:Q", title="Player-seasons"),
        ],
    )
    labels = base.mark_text(dy=-7).encode(
        text=alt.Text("correlation:Q", format=".2f"), color=alt.value("black")
    )
    return alt.layer(base.mark_bar(), labels).properties(
        title=title, width=450, height=220
    )


def chart_opportunity_vs_efficiency_by_position(dfs: dict) -> alt.FacetChart:
    """All positions side by side. dfs maps position -> season-agg DataFrame,
    e.g. {'QB': qb_season_agg, 'RB': rb_season_agg, 'WR': wr_season_agg, 'TE': te_season_agg}.
    """
    t = pd.concat(
        [
            opp_eff_table(corr_features(df, pos), pos).assign(position=pos)
            for pos, df in dfs.items()
        ],
        ignore_index=True,
    )
    base = alt.Chart(t).encode(
        x=alt.X("position:N", sort=list(dfs), title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("metric:N", sort=["Opportunity", "Efficiency"]),
        y=alt.Y(
            "correlation:Q", title="Correlation (r)", scale=alt.Scale(domain=[0, 1.05])
        ),
        color=alt.Color(
            "metric:N",
            scale=OPP_EFF_SCALE,
            legend=alt.Legend(title=None, orient="bottom"),
        ),
        tooltip=[
            "position",
            "when",
            "metric",
            "stat",
            alt.Tooltip("correlation:Q", format=".2f"),
        ],
    )
    labels = base.mark_text(dy=-7, fontSize=10).encode(
        text=alt.Text("correlation:Q", format=".2f"), color=alt.value("black")
    )
    return (
        alt.layer(base.mark_bar(), labels)
        .properties(width=260, height=240)
        .facet(
            column=alt.Column("when:N", sort=["Same season", "Next season"], title=None)
        )
        .properties(title="Opportunity vs. Efficiency by Position")
    )


def chart_driver_scatter(df: pd.DataFrame, position: str) -> alt.LayerChart:
    """Scatter + trend line: the position's main opportunity stat vs fantasy points per game.
    Follows the season filter; r in the subtitle uses all seasons."""
    feats = corr_features(df, position)
    opp = OPP_EFF_SAME[position][0]
    data = feats[["player", "season", "ppg"]].assign(x=feats[opp])
    r = data["x"].corr(data["ppg"])
    base = alt.Chart(data).transform_filter(alt.datum.season == season_filter)
    points = base.mark_circle(
        opacity=0.65, size=70, color=POSITION_COLORS[position]
    ).encode(
        x=alt.X("x:Q", title=opp),
        y=alt.Y("ppg:Q", title="Fantasy Pts / Game"),
        tooltip=[
            "player",
            "season",
            alt.Tooltip("x:Q", title=opp, format=".1f"),
            alt.Tooltip("ppg:Q", title="Fantasy Pts / Game", format=".1f"),
        ],
    )
    trend = (
        base.transform_regression("x", "ppg")
        .mark_line(color="black", strokeDash=[4, 3])
        .encode(x="x:Q", y="ppg:Q")
    )
    return (
        alt.layer(points, trend)
        .add_params(season_filter)
        .properties(
            title=alt.TitleParams(
                f"{position}: {opp} vs. Fantasy Points",
                subtitle=f"r = {r:.2f} across all seasons. Dots and trend line follow the season filter.",
            ),
            width=450,
            height=250,
        )
    )


def chart_efficiency_scatter(df: pd.DataFrame, position: str) -> alt.LayerChart:
    """Scatter + trend line: the position's main efficiency stat vs fantasy points per game.
    Follows the season filter; r in the subtitle uses all seasons."""
    feats = corr_features(df, position)
    opp = OPP_EFF_SAME[position][1]
    data = feats[["player", "season", "ppg"]].assign(x=feats[opp])
    r = data["x"].corr(data["ppg"])
    base = alt.Chart(data).transform_filter(alt.datum.season == season_filter)
    points = base.mark_circle(
        opacity=0.65, size=70, color=POSITION_COLORS[position]
    ).encode(
        x=alt.X("x:Q", title=opp),
        y=alt.Y("ppg:Q", title="Fantasy Pts / Game"),
        tooltip=[
            "player",
            "season",
            alt.Tooltip("x:Q", title=opp, format=".1f"),
            alt.Tooltip("ppg:Q", title="Fantasy Pts / Game", format=".1f"),
        ],
    )
    trend = (
        base.transform_regression("x", "ppg")
        .mark_line(color="black", strokeDash=[4, 3])
        .encode(x="x:Q", y="ppg:Q")
    )
    return (
        alt.layer(points, trend)
        .add_params(season_filter)
        .properties(
            title=alt.TitleParams(
                f"{position}: {opp} vs. Fantasy Points",
                subtitle=f"r = {r:.2f} across all seasons. Dots and trend line follow the season filter.",
            ),
            width=450,
            height=250,
        )
    )


def _correlation_block(df: pd.DataFrame, position: str) -> alt.VConcatChart:
    """2x2 grid: correlations and opportunity-vs-efficiency on top, the two scatters below."""
    return alt.vconcat(
        alt.hconcat(
            chart_driver_correlations(df, position),
            chart_opportunity_vs_efficiency(df, position),
        ),
        alt.hconcat(
            chart_efficiency_scatter(df, position),
            chart_driver_scatter(df, position),
        ),
    )
