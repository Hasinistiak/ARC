import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from open_app import open_app

CLIENT_ID = "108d6ceb140747a69eaeab4c3e8aef13"
CLIENT_SECRET = "94a4ed20dc1e440d90f78f648bbc6d89"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope="user-read-playback-state,user-modify-playback-state"
))

def get_active_device():
    devices = sp.devices()['devices']
    return devices[0]['id'] if devices else None


def play_song(song_name):
    results = sp.search(q=song_name, limit=1, type='track')

    if not results['tracks']['items']:
        print("Song not found.")
        return

    track = results['tracks']['items'][0]
    track_uri = track['uri']

    device_id = get_active_device()

    # If no device → launch Spotify and wait
    if not device_id:
        print("Opening Spotify...")
        open_app("spotify")

        # Wait for Spotify to initialize
        for _ in range(5):
            time.sleep(1)
            device_id = get_active_device()
            if device_id:
                break

    if not device_id:
        print("Still no device found. Open Spotify manually and play once.")
        return

    sp.start_playback(device_id=device_id, uris=[track_uri])

    print(f"Playing: {track['name']} by {track['artists'][0]['name']}")

