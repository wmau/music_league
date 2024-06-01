import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


class Spotify:
    def __init__(self):
        self.spotify = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(),
            requests_timeout=60,
            retries=10,
            backoff_factor=10,
        )

    def find_artist(self, artist_name):
        result = self.spotify.search(artist_name, type="artist", limit=1)["artists"][
            "items"
        ][0]

        return result

    def find_track(self, track_name):
        result = self.spotify.search(track_name, type="track", limit=5)["tracks"][
            "items"
        ]

        return result
