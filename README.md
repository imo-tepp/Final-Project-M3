# FastAPI Banking App

A simple FastAPI-based banking application that allows users to register, login, deposit, withdraw, and check their balance. It is built using SQLite as the database and SQLAlchemy for database operations. The application also includes password hashing using `passlib` for secure user authentication.

## Features

- User registration with hashed password storage
- User login
- Deposit and withdrawal functionalities
- Balance checking
- View all registered users (Admin endpoint)
- Deployed using Docker on an EC2 instance
- Monitored using Prometheus and Grafana

## Prerequisites

- AWS EC2 instance with Docker and Jenkins installed
- Prometheus and Grafana for monitoring

## Jenkins Pipeline Deployment on AWS EC2

### Step 1: Set Up an EC2 Instance

1. **Launch an EC2 Instance**:
   - Go to the AWS Management Console and navigate to EC2.
   - Launch an EC2 instance (Amazon Linux 2 or Ubuntu).
   - Configure the security group to allow inbound traffic on the following ports:
     - **8000** for FastAPI
     - **9090** for Prometheus
     - **3000** for Grafana
     - **8080** for Jenkins
   - Connect to the instance via SSH:

     ```bash
     ssh -i your-key.pem ec2-user@your-ec2-public-ip
     ```

2. **Install Docker on EC2**:
   - SSH into your EC2 instance.
   - Install Docker and start the service:

     ```bash
     sudo yum update -y  # For Amazon Linux 2
     sudo yum install -y docker
     sudo service docker start
     sudo usermod -aG docker ec2-user
     ```

   - Reconnect to the EC2 instance to apply the user group changes:

     ```bash
     ssh -i your-key.pem ec2-user@your-ec2-public-ip
     ```

### Step 2: Install Jenkins on EC2

1. **Install Jenkins**:
   - Add Jenkins to the EC2 instance:

     ```bash
     sudo yum update -y
     sudo wget -O /etc/yum.repos.d/jenkins.repo https://pkg.jenkins.io/redhat-stable/jenkins.repo
     sudo rpm --import https://pkg.jenkins.io/redhat-stable/jenkins.io.key
     sudo yum install -y jenkins java-11-openjdk-devel
     sudo systemctl start jenkins
     sudo systemctl enable jenkins
     ```

   - Jenkins will now be running on port **8080**. Open your web browser and go to:

     ```
     http://<your-ec2-public-ip>:8080
     ```

2. **Set Up Jenkins Initial Configuration**:
   - Retrieve the initial admin password to unlock Jenkins:

     ```bash
     sudo cat /var/lib/jenkins/secrets/initialAdminPassword
     ```

   - Copy the password, paste it into the Jenkins setup wizard, and follow the instructions to set up an admin user.

3. **Install Required Jenkins Plugins**:
   - During the Jenkins setup, install the suggested plugins. After the installation, manually install the following plugins by going to **Manage Jenkins > Manage Plugins** and then **Available**:
     - **GitHub Integration Plugin**
     - **Docker Pipeline Plugin**
     - **SSH Agent Plugin**

### Step 3: Configure Jenkins Credentials

1. **Add SSH Private Key**:
   - Go to **Manage Jenkins > Credentials > System > Global credentials** and add the following credentials:
     - **SSH Private Key**: This will allow Jenkins to SSH into the EC2 instance.
       - Kind: **SSH Username with private key**
       - ID: `ec2-ssh-key`
       - Username: `ec2-user`
       - Private Key: Paste the contents of your private key file (e.g., `your-key.pem`).

2. **Add DockerHub Credentials**:
   - Add your DockerHub username and password for DockerHub integration:
     - Kind: **Username with password**
     - ID: `DockerHub`
     - Username: Your DockerHub username
     - Password: Your DockerHub password

3. **Add GitHub Credentials**:
   - Add your GitHub credentials (or use a GitHub Personal Access Token if required):
     - Kind: **Username with password** (or **Secret Text** for tokens)
     - ID: `GitHub`
     - Username: Your GitHub username
     - Password: Your GitHub password (or token)

### Step 4: Create a Jenkins Pipeline

1. **Create a Pipeline in Jenkins**:
   - In Jenkins, create a new pipeline project and configure it to pull the Jenkinsfile from your version control (GitHub or another repo).
   - Below is the Jenkinsfile that automates the FastAPI deployment:

     ```groovy
     pipeline {
         agent any

         environment {
             DOCKER_IMAGE = "fastapi-app"
             DOCKER_TAG = "${env.BUILD_NUMBER}"
             EC2_INSTANCE = 'ec2-user@your-ec2-public-ip'  // Replace with your EC2 instance's public DNS or IP
         }

         stages {
             stage('Checkout') {
                 steps {
                     checkout scm
                 }
             }

             stage('Install Dependencies') {
                 steps {
                     sh '''
                         python3 -m venv venv
                         source venv/bin/activate
                         pip install -r requirements.txt
                     '''
                 }
             }

             stage('Build Docker Image') {
                 steps {
                     script {
                         docker.build("${DOCKER_IMAGE}:${DOCKER_TAG}")
                         docker.push("${DOCKER_IMAGE}:${DOCKER_TAG}")
                     }
                 }
             }

             stage('Deploy to EC2') {
                 steps {
                     script {
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

             stage('Login to Docker Hub') {
                 steps {
                     script {
                         def username = credentials('DockerHub').getUsername()
                         def password = credentials('DockerHub').getPassword()
                         docker.login("-u $username -p $password")
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
     ```

### Step 5: Configure Prometheus and Grafana on EC2

1. **Install Prometheus**:
   - SSH into the EC2 instance and install Prometheus:

     ```bash
     wget https://github.com/prometheus/prometheus/releases/download/v2.42.0/prometheus-2.42.0.linux-amd64.tar.gz
     tar -xvzf prometheus-2.42.0.linux-amd64.tar.gz
     cd prometheus-2.42.0.linux-amd64
     ```

   - Modify `prometheus.yml` to scrape the FastAPI app running on port 8000:

     ```yaml
     global:
       scrape_interval: 15s

     scrape_configs:
       - job_name: 'fastapi-app'
         static_configs:
           - targets: ['<your-ec2-public-ip>:8000']
     ```

   - Start Prometheus in the background:

     ```bash
     ./prometheus --config.file=prometheus.yml &
     ```

   - Prometheus will be accessible at: `http://<your-ec2-public-ip>:9090`

2. **Install Grafana**:
   - SSH into your EC2 instance and install Grafana:

     ```bash
     sudo apt-get install -y software-properties-common
     sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
     sudo apt-get install -y grafana
     sudo systemctl start grafana-server
     ```

   - Access Grafana at: `http://<your-ec2-public-ip>:3000`

   - Add Prometheus as a data source in Grafana:
     - Go to **Settings > Data Sources > Add Data Source**.
     - Select **Prometheus**.
     - Set URL to your Prometheus instance (e.g., `http://<your-ec2-public-ip>:9090`).
     - Create dashboards for monitoring your FastAPI app.
