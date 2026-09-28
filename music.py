import os
import time

import spotipy
from spotipy.oauth2 import SpotifyOAuth

from open_app import open_app
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = "http://127.0.0.1:8888/callback"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope="user-read-playback-state,user-modify-playback-state",
    )
)


def get_active_device():
    devices = sp.devices()["devices"]

    if not devices:
        return None

    # Prefer an active device
    for device in devices:
        if device.get("is_active"):
            return device["id"]

    return devices[0]["id"]


def play_song(song_name):
    results = sp.search(
        q=song_name,
        limit=1,
        type="track",
    )

    tracks = results["tracks"]["items"]

    if not tracks:
        print("Song not found.")
        return

    track = tracks[0]
    track_uri = track["uri"]

    device_id = get_active_device()

    if not device_id:
        print("Opening Spotify...")
        open_app("spotify")

        for _ in range(10):
            time.sleep(1)

            device_id = get_active_device()

            if device_id:
                break

    if not device_id:
        print("No Spotify device found.")
        return

    sp.start_playback(
        device_id=device_id,
        uris=[track_uri],
    )

    print(
        f"Playing: {track['name']} "
        f"by {track['artists'][0]['name']}"
    )