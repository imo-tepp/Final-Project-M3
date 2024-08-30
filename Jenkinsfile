pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                // Clone the repository
               git credentialsId: 'GitHub_Access', branch: 'main', url: 'https://github.com/imo-tepp/Final-Project-M3.git'

            }
        }
        
        stage('Install Dependencies') {
            steps {
                // Install dependencies
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Test') {
            steps {
                // Run any tests (if you have them)
                sh 'python -m unittest discover -s tests'
            }
        }

        stage('Deploy') {
            steps {
                // Deploy the application (if you’re using Kubernetes or similar)
                sh 'kubectl apply -f k8s/deployment.yaml'
            }
        }
    }

    post {
        always {
            // Cleanup actions (e.g., stopping services)
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
