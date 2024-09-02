pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: 'GitHub_Access', branch: 'main', url: 'https://github.com/imo-tepp/Final-Project-M3.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat 'pip install -r requirements.txt'
            }
        }

        stage('Deploy') {
            steps {
                sh 'kubectl apply -f k8s/deployment.yaml'
            }
        }
    }

    post {
        always {
            echo 'Cleanup...'
        }
        success {
            echo 'Deployment successful!'
        }
        failure {
            echo 'Deployment failed.'
        }
    }
}
