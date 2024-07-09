import pandas as pd
import os

def clean_player_names(df, player_map):
    for col in ["voter_name", "submitter_name"]:
        df[col] = df[col].replace(player_map)

    return df

def build_round_results(df, save_path=None):
    col_list = [
        "league_title",
        "round_number",
        "submitter_name",
        "song_name",
        "voter_name",
        "vote_value",
        "voter_comment"
    ]

    round_results = df[col_list]
    if save_path is not None:
        round_results.to_csv(save_path, index=False)

    return round_results

def build_round_submissions(df, save_path=None):
    cols = [
        "league_title",
        "round_number",
        "submitter_name",
        "song_name",
        "song_artist",
        "song_album",
        "rank",
        "submitter_comment",
        "voted",
    ]

    round_submissions = df[cols].drop_duplicates()
    if save_path is not None:
        round_submissions.to_csv(save_path, index=False)

    return round_submissions

def build_rounds(df, save_path=None):
    cols = [
        "league_title",
        "round_name",
        "round_description",
        "round_number",
    ]
    rounds = df[cols].drop_duplicates()
    if save_path is not None:
        rounds.to_csv(save_path, index=False)

    return rounds

if __name__ == "__main__":
    player_map = {
        "Emma": "Emma Nien",
        "Roger": "Roger Qiu",
        "ben.a.barone": "Ben Barone",
        "Zoe": "Zoe Liao",
        "Harsh": "Harsh Bhatt",
        "Jakob": "Jakob Nicolasora",
        "jtsang527": "Jen Tsang",
        "[Left the league]": "Jenni Podracky",
        "junevwang": "June Wang",
        "Alex": "Alex Chao",
        "jaxiewhoo": "Jackie Wu",
        "tammy": "Tammy Liaw",
        "cjpodracky": "Chris Podracky",
        "iamannamai88": "Anna Mai",
        "Mui": "Alex Mui",
        "michellee.wang": "Michelle Wang",
        "mayurarane": "Mayura Rane",
        "Austin": "Austin Diaz",
    }

    os.chdir(r"C:\Users\Wackie\Documents\GitHub\music_league")
    df = pd.read_csv("./data/full_data.csv")
    df = clean_player_names(df, player_map)

    round_results = build_round_results(df, "./data/round_results.csv")
    round_submissions = build_round_submissions(df, "./data/round_submissions.csv")
    rounds = build_rounds(df, "./data/rounds.csv")


