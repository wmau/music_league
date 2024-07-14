import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os


class Preprocess:
    def __init__(self, player_map, df_path="./data/full_data.csv"):
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(),
            requests_timeout=20,
            retries=5,
            backoff_factor=20,
        )

        self.df = pd.read_csv(df_path)
        self.df = self.clean_player_names(player_map)

    def clean_player_names(self, player_map):
        for col in ["voter_name", "submitter_name"]:
            self.df[col] = self.df[col].replace(player_map)

        return self.df

    @staticmethod
    def build_round_results(self, save_path=None):
        col_list = [
            "league_title",
            "round_number",
            "submitter_name",
            "song_name",
            "voter_name",
            "vote_value",
            "voter_comment",
        ]

        round_results = self.df[col_list]
        if save_path is not None:
            round_results.to_csv(save_path, index=False)

        return round_results

    def build_round_submissions(self, save_path=None):
        cols = [
            "league_title",
            "round_number",
            "submitter_name",
            "song_name",
            "song_artist",
            "song_album",
            "spotify_link",
            "rank",
            "submitter_comment",
            "voted",
        ]

        round_submissions = self.df[cols].drop_duplicates().reset_index(drop=True)

        # Get song ID
        round_submissions["song_id"] = (
            round_submissions["spotify_link"]
            .str.split("https://open.spotify.com/track/")
            .str[-1]
        )

        # Enrich with Spotify data.
        round_submissions = self.get_track_data(round_submissions)
        round_submissions = self.get_artist_data(round_submissions)
        round_submissions = self.get_audio_features(round_submissions)

        for col in ["song_popularity", "artist_popularity"]:
            round_submissions[col] = round_submissions[col].astype(int)

        if save_path is not None:
            round_submissions.to_csv(save_path, index=False)

        return round_submissions

    def get_track_data(self, round_submissions):
        chunk_size = 50
        artist_ids = pd.DataFrame()
        for start in range(0, len(round_submissions), chunk_size):
            tracks = self.spotify.tracks(
                round_submissions.iloc[start : start + chunk_size]["song_id"]
            )

            # Get song popularity
            round_submissions.loc[start : start + chunk_size - 1, "song_popularity"] = [
                int(track["popularity"]) for track in tracks["tracks"]
            ]

            # Compile artist IDs
            artist_ids = pd.concat(
                (
                    artist_ids,
                    pd.DataFrame(
                        {
                            "artist_ids": [
                                [artist["id"] for artist in track["artists"]]
                                for track in tracks["tracks"]
                            ]
                        }
                    ),
                )
            )

        # Put artist IDs into a column.
        round_submissions["artist_ids"] = artist_ids.reset_index(drop=True)

        # Get primary artist IDs
        round_submissions["primary_artist_id"] = round_submissions["artist_ids"].apply(
            lambda x: x[0]
        )

        return round_submissions

    def get_artist_data(self, round_submissions):
        chunk_size = 50
        genres = pd.DataFrame()
        for start in range(0, len(round_submissions), chunk_size):
            artists = self.spotify.artists(
                round_submissions.iloc[start : start + chunk_size]["primary_artist_id"]
            )

            # Get artist popularity
            round_submissions.loc[
                start : start + chunk_size - 1, "artist_popularity"
            ] = [int(artist["popularity"]) for artist in artists["artists"]]

            # Compile genres
            genres = pd.concat(
                (
                    genres,
                    pd.DataFrame(
                        {"genres": [artist["genres"] for artist in artists["artists"]]}
                    ),
                )
            )

        # Put artist IDs into a column.
        round_submissions["genres"] = genres.reset_index(drop=True)

        return round_submissions

    def get_audio_features(self, round_submissions):
        chunk_size = 100
        all_audio_features = pd.DataFrame()
        for start in range(0, len(round_submissions), chunk_size):
            audio_features = self.spotify.audio_features(
                round_submissions.iloc[start : start + chunk_size]["song_id"]
            )

            all_audio_features = pd.concat(
                (all_audio_features, pd.DataFrame(audio_features)), axis=0
            )

        all_audio_features = all_audio_features.drop(
            ["type", "uri", "analysis_url"], axis=1
        )
        round_submissions = pd.merge(
            left=round_submissions,
            right=all_audio_features,
            how="left",
            left_on="song_id",
            right_on="id",
        )
        round_submissions.drop(["id"], axis=1, inplace=True)

        return round_submissions

    def build_rounds(self, save_path=None):
        cols = [
            "league_title",
            "round_name",
            "round_description",
            "round_number",
        ]
        rounds = self.df[cols].drop_duplicates()
        if save_path is not None:
            rounds.to_csv(save_path, index=False)

        return rounds

    def run(self, save_path=None):
        if save_path is not None:
            save_paths = {
                table_type: os.path.join(table_type + ".csv")
                for table_type in ["round_results", "round_submissions", "rounds"]
            }
        else:
            save_paths = {
                table_type: None
                for table_type in ["round_results", "round_submissions", "rounds"]
            }

        round_results = self.build_round_results(save_paths["round_results"])
        round_submissions = self.build_round_submissions(save_paths["round_submissions"])
        rounds = self.build_rounds(save_paths["rounds"])

        return round_results, round_submissions, rounds
