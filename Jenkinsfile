pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('Pull Docker Image') {
            steps {
                sh 'docker pull ashish453/spotify-automation:latest'
            }
        }

        stage('Run Spotify Automation') {
            steps {
                withCredentials([
                    string(credentialsId: 'spotify-client-id',
                           variable: 'SPOTIFY_CLIENT_ID'),
                    string(credentialsId: 'spotify-client-secret',
                           variable: 'SPOTIFY_CLIENT_SECRET'),
                    string(credentialsId: 'spotify-refresh-token',
                           variable: 'SPOTIFY_REFRESH_TOKEN'),
                    string(credentialsId: 'spotify-playlist-id',
                           variable: 'SPOTIFY_PLAYLIST_ID'),
                    string(credentialsId: 'spotify-artist-id',
                           variable: 'SPOTIFY_ARTIST_ID')
                ]) {
                    sh '''
                    docker run --rm ^
                      -e SPOTIFY_CLIENT_ID ^
                      -e SPOTIFY_CLIENT_SECRET ^
                      -e SPOTIFY_REFRESH_TOKEN ^
                      -e SPOTIFY_PLAYLIST_ID ^
                      -e SPOTIFY_ARTIST_ID ^
                      ashish453/spotify-automation:latest
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Spotify automation completed.'
        }
        failure {
            echo 'Spotify automation failed. Check the logs.'
        }
    }
}
