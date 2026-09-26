pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                echo 'Cloning repository'
                git branch: 'master', url: 'https://github.com/darshanshi-waghela/DEVOPS-ASSIGNMENT.git'
            }
        }

        stage('Test - Event Service') {
            steps {
                dir('event-service') {
                    bat 'pip install -r requirements.txt'
                    bat 'pytest'
                }
            }
        }

        stage('Test - Customer Service') {
            steps {
                dir('customer-service') {
                    bat 'pip install -r requirements.txt'
                    bat 'pytest'
                }
            }
        }

        stage('Test - Booking Service') {
            steps {
                dir('booking-service') {
                    bat 'pip install -r requirements.txt'
                    bat 'pytest'
                }
            }
        }

        stage('Build Docker Images') {
            steps {
                echo 'Building versioned images for all 3 microservices'
                bat 'docker build -t event-service:%BUILD_NUMBER% ./event-service'
                bat 'docker build -t customer-service:%BUILD_NUMBER% ./customer-service'
                bat 'docker build -t booking-service:%BUILD_NUMBER% ./booking-service'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying the updated stack with docker-compose'
                bat 'docker-compose down'
                bat 'docker-compose up -d --build'
            }
        }
    }

    post {
        success {
            echo 'All 3 microservices were built, tested and deployed successfully!'
        }
        failure {
            echo 'Pipeline failed - check the stage logs above.'
        }
    }
}
