import pandas as pd
from query_spotify import Spotify
import time

S = Spotify()
round_submissions = pd.read_csv("data/round_submissions.csv")

genres, artist_popularity = [], []
retry_count = 10
for artist, song_name in zip(
    round_submissions["song_artist"], round_submissions["song_name"]
):
    while retry_count != 0:
        try:
            artist_result = S.find_artist(artist)
            artist_popularity.append(artist_result["popularity"])
            genres.append(artist_result["genres"])
        except Exception as e:
            print(f"Error encountered: {e}")
            retry_count -= 1
            time.sleep(1)
        retry_count = 10

enriched = round_submissions.copy()
enriched["genres"] = genres
enriched["artist_popularity"] = artist_popularity
