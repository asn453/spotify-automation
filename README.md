# Spotify Playlist Automation

A Python-based automation project that uses the Spotify Web API to identify tracks released by a specified artist that are missing from a target Spotify playlist. The application compares track IDs, filters duplicate song names, and can add missing tracks when explicitly enabled.

The project uses Docker to package the application, GitHub Actions to build and publish the Docker image, and Jenkins to execute the automation pipeline.

## Features

- **Spotify API integration:** Authenticates using Spotify OAuth refresh tokens.
- **Automatic track discovery:** Retrieves an artist's albums and singles, then collects their tracks.
- **Playlist comparison:** Compares track IDs against the selected playlist to identify missing tracks.
- **Duplicate filtering:** Filters duplicate song names before preparing additions.
- **Pagination support:** Handles API responses containing multiple pages of results.
- **Rate-limit handling:** Retries certain temporary errors and respects Spotify's `Retry-After` response.
- **Dry-run mode:** Shows which tracks would be added without modifying the playlist by default.
- **Docker containerization:** Packages the Python application and its dependencies.
- **CI/CD integration:** Uses GitHub Actions to build and push the image to Docker Hub, with Jenkins executing the containerized application.

## Tech Stack

- **Language:** Python
- **API:** Spotify Web API
- **Libraries:** Requests, python-dotenv
- **Containerization:** Docker
- **Container Registry:** Docker Hub
- **CI/CD:** GitHub Actions, Jenkins
- **Version Control:** Git, GitHub

## How It Works

1. Loads Spotify credentials and configuration from environment variables.
2. Requests an access token using the Spotify refresh token.
3. Retrieves the target playlist and its existing tracks.
4. Fetches albums and singles associated with the selected artist.
5. Collects the artist's tracks and compares them against the playlist.
6. Identifies tracks that are missing and filters duplicate song names.
7. Prints the proposed additions in dry-run mode.
8. Adds the missing tracks only when `SPOTIFY_APPLY_CHANGES=true`.

## Project Architecture

```text
Developer
   |
   v
GitHub Repository
   |
   | Push to main
   v
GitHub Actions
   |
   | Build and push Docker image
   v
Docker Hub
   |
   | Jenkins pulls image
   v
Jenkins Pipeline
   |
   | Injects credentials
   v
Docker Container
   |
   v
Python Spotify Automation
   |
   v
Spotify Web API
   |
   v
Compare Tracks and Report Results
```

## Repository Structure

```text
spotify-automation/
├── .github/
│   └── workflows/
│       └── docker-build-push.yml
├── Dockerfile
├── Jenkinsfile
├── requirements.txt
├── spotify.py
└── README.md
```

## Prerequisites

- Python 3.12 or compatible environment
- A Spotify account and a Spotify developer application
- Spotify API credentials and a refresh token
- Docker
- Git and GitHub
- Docker Hub account
- Jenkins, if running the CI/CD pipeline

## Configuration

Configure the following environment variables. Keep their values private and never commit credentials to GitHub.

| Variable | Purpose |
|---|---|
| `SPOTIFY_CLIENT_ID` | Spotify application client ID |
| `SPOTIFY_CLIENT_SECRET` | Spotify application client secret |
| `SPOTIFY_REFRESH_TOKEN` | OAuth refresh token |
| `SPOTIFY_PLAYLIST_ID` | Target playlist ID |
| `SPOTIFY_ARTIST_ID` | Artist whose tracks will be collected |
| `SPOTIFY_APPLY_CHANGES` | Controls whether missing tracks are added |

Set `SPOTIFY_APPLY_CHANGES=false` to perform a dry run. Set it to `true` only when you are ready to modify the playlist.

For local development, use a `.env` file and ensure it is included in `.gitignore`.

## Run Locally

1. Clone the repository:

   ```bash
   git clone https://github.com/asn453/spotify-automation.git
   cd spotify-automation
   ```

2. Create and activate a Python virtual environment.

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure the required environment variables.

5. Run the application:

   ```bash
   python spotify.py
   ```

## Run with Docker

Build the image:

```bash
docker build -t spotify-automation .
```

Run it in dry-run mode, supplying your environment variables securely through your local environment or an environment file:

```bash
docker run --rm --env-file .env \
  -e SPOTIFY_APPLY_CHANGES=false \
  spotify-automation
```

Review the output before enabling playlist modifications. Avoid placing secret values directly in commands that may be saved in shell history.

## CI/CD Pipeline

### GitHub Actions

- Triggers when relevant application or workflow files are pushed to the `main` branch.
- Builds the Docker image.
- Authenticates to Docker Hub using GitHub repository secrets.
- Publishes the image as `ashish453/spotify-automation:latest`.

Configure these GitHub repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

### Jenkins

- Retrieves the latest Docker image from Docker Hub.
- Reads Spotify credentials from Jenkins Credentials.
- Passes the credentials and execution settings into the container.
- Runs the automation and displays the output in the Jenkins console log.

The current pipeline uses dry-run mode by default, so a successful build does not necessarily mean the playlist was modified.

## Security

- Never commit `.env` files, access tokens, refresh tokens, or client secrets.
- Store CI/CD credentials in GitHub Actions secrets and Jenkins Credentials.
- Keep dry-run mode enabled until you have reviewed the proposed changes.
- Use a dedicated development playlist when testing write operations.

## Learning Objectives

This project provides practical experience with:

- Python scripting and API integration
- OAuth authentication and environment variables
- HTTP requests, pagination, and error handling
- Docker images and containers
- GitHub Actions workflows
- Jenkins declarative pipelines
- CI/CD automation and secret management

## Future Improvements

- Add automated unit tests.
- Add structured logging and clearer error reporting.
- Schedule regular executions through Jenkins.
- Improve duplicate detection to handle alternate versions and remixes.
- Add notifications summarizing tracks added during each run.

## License

Add a license file if you intend to distribute this project for reuse.
