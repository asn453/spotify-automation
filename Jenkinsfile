pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
    }

    environment {
        SPOTIFY_APPLY_CHANGES = 'false'
    }

    stages {
        stage('Check Docker') {
            steps {
                sh 'docker --version'
                sh 'docker ps'
            }
        }

        stage('Pull Docker Image') {
            steps {
                sh 'docker pull ashish453/spotify-automation:latest'
            }
        }

        stage('Run Spotify Automation') {
            steps {
                withCredentials([
                    string(credentialsId: 'SPOTIFY_CLIENT_ID',
                           variable: 'SPOTIFY_CLIENT_ID'),
                    string(credentialsId: 'SPOTIFY_CLIENT_SECRET',
                           variable: 'SPOTIFY_CLIENT_SECRET'),
                    string(credentialsId: 'SPOTIFY_REFRESH_TOKEN',
                           variable: 'SPOTIFY_REFRESH_TOKEN'),
                    string(credentialsId: 'SPOTIFY_PLAYLIST_ID',
                           variable: 'SPOTIFY_PLAYLIST_ID'),
                    string(credentialsId: 'SPOTIFY_ARTIST_ID',
                           variable: 'SPOTIFY_ARTIST_ID')
                ]) {
                    sh '''
                        docker run --rm \
                          -e SPOTIFY_CLIENT_ID \
                          -e SPOTIFY_CLIENT_SECRET \
                          -e SPOTIFY_REFRESH_TOKEN \
                          -e SPOTIFY_PLAYLIST_ID \
                          -e SPOTIFY_ARTIST_ID \
                          -e SPOTIFY_APPLY_CHANGES \
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