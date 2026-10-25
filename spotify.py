import time
import os
import requests
from dotenv import load_dotenv

# 1. Load configuration from .env
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.getenv("SPOTIFY_REFRESH_TOKEN")
PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")
ARTIST_ID = os.getenv("SPOTIFY_ARTIST_ID")


def spotify_request(method, url, max_retries=5, **kwargs):
    """Make a Spotify request (GET/POST) with retry handling.

    FIX 1: the original function called itself (spotify_get -> spotify_get)
    which causes infinite recursion. It must call requests.request().
    """

    kwargs.setdefault("timeout", 30)

    for attempt in range(max_retries):
        try:
            response = requests.request(method, url, **kwargs)

            # Spotify rate limit: wait before retrying.
            if response.status_code == 429:
                wait = float(response.headers.get("Retry-After", "5"))
                if attempt == max_retries - 1:
                    response.raise_for_status()

                print(f"Rate limited. Waiting {wait} seconds...")
                time.sleep(wait)
                continue

            # FIX 3: temporary server errors are now actually retried.
            # Originally raise_for_status() was called right away, so the
            # code crashed instead of retrying.
            if response.status_code in (500, 502, 503, 504):
                if attempt == max_retries - 1:
                    response.raise_for_status()

                wait = min(2 ** attempt, 30)
                print(
                    f"Server error {response.status_code}. "
                    f"Retrying in {wait} seconds "
                    f"({attempt + 1}/{max_retries})..."
                )
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response

        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
        ):
            if attempt == max_retries - 1:
                raise

            wait = min(2 ** attempt, 30)
            print(
                f"Connection failed. Retrying in {wait} seconds "
                f"({attempt + 1}/{max_retries})..."
            )
            time.sleep(wait)

    raise RuntimeError("Spotify request failed after retries.")


def spotify_get(url, headers=None, params=None, **kwargs):
    """Convenience wrapper for GET requests."""
    return spotify_request("GET", url, headers=headers, params=params, **kwargs)


def get_access_token():
    """Exchange the refresh token for a fresh access token."""

    # FIX 2: the token endpoint requires POST, not GET. The original sent
    # auth= and data= to spotify_get, which doesn't accept them.
    response = spotify_request(
        "POST",
        "https://accounts.spotify.com/api/token",
        auth=(CLIENT_ID, CLIENT_SECRET),
        data={
            "grant_type": "refresh_token",
            "refresh_token": REFRESH_TOKEN,
        },
    )

    return response.json()["access_token"]


def test_playlist_access(access_token):
    """Retrieve the target playlist details."""

    response = spotify_get(
        f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    return response.json()


def get_album_tracks(access_token, album_id):
    """Retrieve all tracks from an album, handling pagination."""

    tracks = []
    url = f"https://api.spotify.com/v1/albums/{album_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 50}

    while url:
        response = spotify_get(url, headers=headers, params=params)
        data = response.json()

        tracks.extend(data.get("items", []))

        # Continue if Spotify provides another page.
        url = data.get("next")
        params = None  # the "next" URL already contains the params

    return tracks


def get_playlist_tracks(access_token):
    """Retrieve all tracks currently in the target playlist."""

    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}/items"
    headers = {"Authorization": f"Bearer {access_token}"}
    params = {"limit": 10}

    while url:
        response = spotify_get(url, headers=headers, params=params)
        data = response.json()

        for entry in data.get("items", []):
            # Handle current and older Spotify response formats.
            track = entry.get("item") or entry.get("track")

            if track and track.get("id"):
                tracks.append(track)

        url = data.get("next")
        params = None

    return tracks


def get_all_artist_tracks(access_token):
    """Collect tracks from all albums and singles for the artist."""

    headers = {"Authorization": f"Bearer {access_token}"}

    # Step 1: Fetch every page of the artist's albums and singles.
    url = f"https://api.spotify.com/v1/artists/{ARTIST_ID}/albums"
    params = {
        "include_groups": "album,single",
        "limit": 10,
    }

    albums = []
    seen_album_ids = set()

    while url:
        response = spotify_get(url, headers=headers, params=params)
        data = response.json()

        for album in data.get("items", []):
            album_id = album.get("id")

            if album_id and album_id not in seen_album_ids:
                seen_album_ids.add(album_id)
                albums.append(album)

        url = data.get("next")
        params = None

    print("Albums and singles found:", len(albums))

    # Step 2: Fetch tracks from every album.
    all_tracks = []
    seen_track_ids = set()

    for index, album in enumerate(albums, start=1):
        print(
            f"Fetching album {index}/{len(albums)}:",
            album.get("name", "Unknown album"),
        )

        album_tracks = get_album_tracks(access_token, album["id"])

        for track in album_tracks:
            track_id = track.get("id")

            # Avoid collecting the same Spotify track ID twice.
            if track_id and track_id not in seen_track_ids:
                seen_track_ids.add(track_id)
                all_tracks.append(track)

    print("Unique tracks collected:", len(all_tracks))

    return all_tracks


def normalize(name):
    """Lowercase and trim a song name so near-identical names match."""
    return " ".join((name or "").lower().split())


def add_tracks_to_playlist(access_token, track_uris):
    """Add tracks to the playlist, 100 at a time (Spotify's limit)."""

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    url = f"https://api.spotify.com/v1/playlists/{PLAYLIST_ID}/items"

    for start in range(0, len(track_uris), 100):
        chunk = track_uris[start:start + 100]
        spotify_request("POST", url, headers=headers, json={"uris": chunk})
        print(f"Added {start + len(chunk)}/{len(track_uris)} tracks...")


# 2. Execute the program only when this file is run directly.
if __name__ == "__main__":

    # Step A: Validate required configuration.
    required = {
        "SPOTIFY_CLIENT_ID": CLIENT_ID,
        "SPOTIFY_CLIENT_SECRET": CLIENT_SECRET,
        "SPOTIFY_REFRESH_TOKEN": REFRESH_TOKEN,
        "SPOTIFY_PLAYLIST_ID": PLAYLIST_ID,
        "SPOTIFY_ARTIST_ID": ARTIST_ID,
    }

    missing = [name for name, value in required.items() if not value]

    if missing:
        raise RuntimeError(f"Missing settings in .env: {', '.join(missing)}")

    # Step B: Authenticate with Spotify.
    print("Getting a new access token...")
    token = get_access_token()
    print("Access token received successfully.")

    # Step C: Check playlist access.
    print("\nChecking playlist access...")
    playlist = test_playlist_access(token)

    print("Playlist access successful!")
    print("Playlist name:", playlist.get("name", "Unknown"))
    print("Playlist ID:", playlist.get("id", "Unknown"))

    # Step D: Retrieve current playlist tracks.
    print("\nChecking current playlist tracks...")
    playlist_tracks = get_playlist_tracks(token)

    print("Tracks currently in playlist:", len(playlist_tracks))

    for track in playlist_tracks:
        print("-", track.get("name", "Unknown track"))

    # Step E: Collect tracks from all albums and singles.
    print("\nCollecting all tracks...")
    all_tracks = get_all_artist_tracks(token)

    # Step F: Compare artist tracks with playlist tracks.
    print("\nComparing tracks with the playlist...")

    playlist_track_ids = {
        track["id"] for track in playlist_tracks if track.get("id")
    }

    missing_tracks = [
        track for track in all_tracks if track["id"] not in playlist_track_ids
    ]

    print("Unique artist tracks:", len(all_tracks))
    print("Tracks already in playlist:", len(playlist_track_ids))
    print("Tracks missing from playlist:", len(missing_tracks))

    # The same song can exist on an album AND a single with different IDs,
    # so also skip songs whose name is already in the playlist, and skip
    # duplicate names within the missing list itself.
    existing_names = {normalize(t.get("name")) for t in playlist_tracks}
    to_add = []
    seen_names = set()

    for track in missing_tracks:
        key = normalize(track.get("name"))
        if key in existing_names or key in seen_names:
            continue
        seen_names.add(key)
        to_add.append(track)

    print("\nSongs to add to the playlist:", len(to_add))

    for track in to_add:
        print("-", track.get("name", "Unknown track"), "|", track.get("id", "No ID"))

    # Step G: Add the missing songs (asks before changing anything).
    if to_add:
        apply_changes = (
            os.getenv("SPOTIFY_APPLY_CHANGES", "false").lower() == "true"
        )

    if apply_changes:
        add_tracks_to_playlist(token, [t["uri"] for t in to_add])
        print("Done! Playlist updated.")
    else:
        print("Dry run: Nothing was changed.")
        print("Set SPOTIFY_APPLY_CHANGES=true to add songs.")
else:
    print("Playlist is already up to date.")