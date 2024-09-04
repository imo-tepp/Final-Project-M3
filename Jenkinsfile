pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "riajul98/fastapi-app"  // Use your Docker Hub username here
        DOCKER_TAG = "${env.BUILD_NUMBER}"
        EC2_INSTANCE = 'ec2-user@ec2-52-211-185-123.eu-west-1.compute.amazonaws.com'  //EC2 instance's public DNS
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
                sh '''
                    python3 -m venv venv
                    source venv/bin/activate
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Login to Docker Hub') {
            steps {
                script {
                    // Login to Docker Hub using Jenkins credentials
                    withCredentials([usernamePassword(credentialsId: 'DockerHub', usernameVariable: 'DOCKERHUB_USER', passwordVariable: 'DOCKERHUB_PASS')]) {
                        sh 'docker login -u $DOCKERHUB_USER -p $DOCKERHUB_PASS'
                    }
                }
            }
        }

        stage('Build and Push Docker Image') {
            steps {
                script {
                    // Build and Push the Docker image for the FastAPI app
                    sh '''
                        docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} .
                        docker push ${DOCKER_IMAGE}:${DOCKER_TAG}
                    '''
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
                                docker pull ${DOCKER_IMAGE}:${DOCKER_TAG}
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
