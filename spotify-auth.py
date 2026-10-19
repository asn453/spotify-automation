import base64
import secrets
import threading
import webbrowser
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs

import requests

# Spotify app configuration
CLIENT_ID = input("Enter your Spotify Client ID: ").strip()
CLIENT_SECRET = input("Enter your Spotify Client Secret: ").strip()

REDIRECT_URI = "http://127.0.0.1:8888/callback"

SCOPES = [
    "playlist-modify-private",
    "playlist-modify-public",
    "playlist-read-private",
]

# Random value used to protect the OAuth callback
STATE = secrets.token_urlsafe(32)

authorization_code = None
callback_error = None


class SpotifyCallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global authorization_code, callback_error

        query = parse_qs(urlparse(self.path).query)

        if urlparse(self.path).path != "/callback":
            self.send_error(404)
            return

        returned_state = query.get("state", [None])[0]

        if returned_state != STATE:
            self.send_error(400, "Invalid OAuth state")
            return

        callback_error = query.get("error", [None])[0]
        authorization_code = query.get("code", [None])[0]

        if callback_error or not authorization_code:
            message = b"Spotify authorization failed. You may close this tab."
            self.send_response(400)
        else:
            message = b"Spotify authorization received. You may close this tab."
            self.send_response(200)

        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(message)))
        self.end_headers()
        self.wfile.write(message)

    def log_message(self, format, *args):
        pass


if not CLIENT_ID or not CLIENT_SECRET:
    raise ValueError("Client ID and Client Secret are required.")

# Start the local callback server
server = HTTPServer(("127.0.0.1", 8888), SpotifyCallbackHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()

try:
    # Build Spotify authorization URL
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": STATE,
    }

    auth_url = (
        "https://accounts.spotify.com/authorize?"
        + urlencode(params)
    )

    print("Opening Spotify authorization in your browser...")
    webbrowser.open(auth_url)

    print("Waiting for you to authorize the application...")
    while authorization_code is None and callback_error is None:
        threading.Event().wait(0.2)

    if callback_error:
        raise RuntimeError(f"Spotify authorization failed: {callback_error}")

    # Exchange the authorization code for tokens
    credentials = base64.b64encode(
        f"{CLIENT_ID}:{CLIENT_SECRET}".encode()
    ).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": REDIRECT_URI,
        },
        timeout=30,
    )

    response.raise_for_status()
    tokens = response.json()

    print("\nAuthorization successful!")
    print("Access token received:", bool(tokens.get("access_token")))
    print("Refresh token received:", bool(tokens.get("refresh_token")))
    print("Granted scopes:", tokens.get("scope", "(not returned)"))


    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        raise RuntimeError("Spotify did not return a refresh token.")

    env_path = Path(".env")

    # Read existing configuration, if present.
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    # Remove any old refresh-token entry.
    lines = [
        line for line in lines
        if not line.startswith("SPOTIFY_REFRESH_TOKEN=")
    ]

    # Add the new refresh token.
    lines.append(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")

    # Save the configuration without deleting other settings.
    env_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8"
    )

    print("Refresh token saved to .env")


finally:
    server.shutdown()
    server.server_close()
