pipeline {
    agent any

    environment {
        DOCKER_IMAGE = 'fastapi-app'  // Just use a local name for your image
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        EC2_INSTANCE = 'ec2-user@ec2-3-8-203-126.eu-west-2.compute.amazonaws.com'  //EC2 instance's public DNS
    }

    stages {
        stage('Checkout') {
            steps {
                // Checkout the latest code from your repository
                checkout scm
            }
        }

        stage('Install Dependencies') {
            steps {
                // Install the required Python packages
                sh 'pip install -r requirements.txt'
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Build the Docker image for the FastAPI app
                    docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                }
            }
        }

        stage('Deploy to EC2') {
            steps {
                script {
                    // SSH into the EC2 instance and deploy the Docker container
                    sshagent(['ec2-ssh-key']) {
                        sh """
                            ssh -o StrictHostKeyChecking=no ${EC2_INSTANCE} '
                                docker stop fastapi-app || true
                                docker rm fastapi-app || true
                                docker run -d --name fastapi-app -p 8000:8000 ${DOCKER_IMAGE}:${DOCKER_TAG}
                            '
                        """
                    }
                }
            }
        }
    }

    post {
        always {
            echo 'Cleaning up...'
        }
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed.'
        }
    }
}
