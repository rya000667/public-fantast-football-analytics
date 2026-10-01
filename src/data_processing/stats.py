import pandas as pd



def calculate_mean_passing_stats_by_year(df:pd.DataFrame, year:int)-> tuple[float, float, float, float, float, float]:
    """
    """
    # filter for specified year
    season_df = df[df['season']==year]

    # get stats 
    avg_total_games_played = season_df['total_games_played'].mean()
    avg_completions = season_df['completions'].mean()
    avg_passing_yards = season_df['passing_yards'].mean()
    avg_passing_tds = season_df['passing_tds'].mean()
    avg_passing_interceptions = season_df['passing_interceptions'].mean()
    avg_passing_yards_per_game = season_df['passing_yards_per_game'].mean()

    return (avg_total_games_played, avg_completions, avg_passing_yards, avg_passing_tds, avg_passing_interceptions, avg_passing_yards_per_game)