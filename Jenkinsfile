pipeline {
    agent any

    parameters {
        string(name: 'DOCKER_REGISTRY', defaultValue: 'docker.io', description: 'Docker registry')
        string(name: 'DOCKER_USERNAME', defaultValue: 'paambust', description: 'Docker Hub username')
        string(name: 'IMAGE_TAG', defaultValue: 'latest', description: 'Docker image tag')
        booleanParam(name: 'PUSH_IMAGES', defaultValue: false, description: 'Push multi-arch images to Docker Hub')
    }

    environment {
        WORKSPACE_ROOT = "${WORKSPACE}"
        COMPOSE_FILE = "${WORKSPACE}/docker-compose.yml"
        IMAGE_API = "${DOCKER_REGISTRY}/${DOCKER_USERNAME}/ai-log-analyzer-api"
        IMAGE_WORKER = "${DOCKER_REGISTRY}/${DOCKER_USERNAME}/ai-log-analyzer-worker"
        // Credentials for Docker Hub authentication
        DOCKER_HUB_CREDENTIALS = credentials('docker-hub-credentials')
    }

    stages {
        stage('Checkout') {
            steps {
                echo "Checking out repository..."
                checkout scm
                sh 'git log -1 --pretty=%B'
            }
        }

        stage('Build Services') {
            steps {
                echo "Building Docker images from docker-compose..."
                sh '''
                    cd ${WORKSPACE_ROOT}
                    docker-compose build --no-cache
                '''
            }
        }

        stage('Start Services') {
            steps {
                echo "Starting services with docker-compose..."
                sh '''
                    cd ${WORKSPACE_ROOT}
                    docker-compose up -d
                    echo "Waiting for services to be ready..."
                    sleep 5
                '''
            }
        }

        stage('Health Checks & Tests') {
            steps {
                echo "Running health checks and tests..."
                sh '''
                    cd ${WORKSPACE_ROOT}
                    # Install test dependencies
                    echo "Installing test dependencies..."
                    pip install -r tests/requirements.txt --quiet
                    
                    # Run integration tests
                    echo "Running integration tests..."
                    python3 tests/test_api.py
                    echo "All tests passed!"
                '''
            }
        }

        stage('View Logs') {
            steps {
                echo "Service logs for debugging (if needed)..."
                sh '''
                    echo "=== API Service Logs ==="
                    docker-compose logs api || echo "No logs available"
                    echo ""
                    echo "=== Worker Service Logs ==="
                    docker-compose logs worker || echo "No logs available"
                    echo ""
                    echo "=== Database Logs ==="
                    docker-compose logs postgres || echo "No logs available"
                '''
            }
        }

        stage('Cleanup Local Services') {
            steps {
                echo "Shutting down docker-compose services..."
                sh '''
                    cd ${WORKSPACE_ROOT}
                    docker-compose down -v || true
                '''
            }
        }

        stage('Build Multi-Arch Images') {
            when {
                expression { params.PUSH_IMAGES == true }
            }
            steps {
                echo "Building multi-architecture Docker images (AMD64 + ARM64)..."
                sh '''
                    cd ${WORKSPACE_ROOT}
                    
                    # Check if buildx is available
                    docker buildx version || {
                        echo "Setting up docker buildx..."
                        docker buildx create --use || true
                    }
                    
                    # Login to Docker Hub using Jenkins credentials
                    echo "Authenticating to Docker Hub..."
                    echo "${DOCKER_HUB_CREDENTIALS_PSW}" | docker login -u "${DOCKER_HUB_CREDENTIALS_USR}" --password-stdin ${DOCKER_REGISTRY}
                    
                    # Build and push API image
                    echo "Building API image for amd64,arm64..."
                    docker buildx build \
                        --platform linux/amd64,linux/arm64 \
                        -t ${IMAGE_API}:${IMAGE_TAG} \
                        -t ${IMAGE_API}:latest \
                        --push \
                        -f ./api/Dockerfile \
                        ./api
                    
                    # Build and push Worker image
                    echo "Building Worker image for amd64,arm64..."
                    docker buildx build \
                        --platform linux/amd64,linux/arm64 \
                        -t ${IMAGE_WORKER}:${IMAGE_TAG} \
                        -t ${IMAGE_WORKER}:latest \
                        --push \
                        -f ./worker/Dockerfile \
                        ./worker
                    
                    # Logout from Docker Hub (security best practice)
                    echo "Logging out from Docker Hub..."
                    docker logout
                    
                    echo "Multi-arch images built and pushed successfully!"
                '''
            }
        }

        stage('Docker Hub Summary') {
            when {
                expression { params.PUSH_IMAGES == true }
            }
            steps {
                echo "Build Summary"
                sh '''
                    echo "======================================"
                    echo "Multi-Arch Images Published to Docker Hub:"
                    echo "======================================"
                    echo "API Service:    ${IMAGE_API}:${IMAGE_TAG}"
                    echo "Worker Service: ${IMAGE_WORKER}:${IMAGE_TAG}"
                    echo "Platforms: linux/amd64, linux/arm64"
                    echo "======================================"
                '''
            }
        }

        stage('Cleanup Docker Images') {
            when {
                expression { params.PUSH_IMAGES == true }
            }
            steps {
                echo "Cleaning up local Docker images..."
                sh '''
                    echo "Removing local image copies (already pushed to Docker Hub)..."
                    
                    # Remove API images
                    docker rmi -f ${IMAGE_API}:${IMAGE_TAG} 2>/dev/null || echo "API image ${IMAGE_TAG} not found locally"
                    docker rmi -f ${IMAGE_API}:latest 2>/dev/null || echo "API image latest not found locally"
                    
                    # Remove Worker images
                    docker rmi -f ${IMAGE_WORKER}:${IMAGE_TAG} 2>/dev/null || echo "Worker image ${IMAGE_TAG} not found locally"
                    docker rmi -f ${IMAGE_WORKER}:latest 2>/dev/null || echo "Worker image latest not found locally"
                    
                    # Optional: Remove dangling images
                    echo "Removing dangling images..."
                    docker image prune -f --filter "dangling=true" || true
                    
                    echo "Cleanup completed!"
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline execution completed."
            sh '''
                echo "Cleaning up any remaining containers..."
                docker-compose down -v 2>/dev/null || true
                
                echo "Removing build artifacts and temporary images..."
                docker image prune -f --filter "dangling=true" 2>/dev/null || true
            '''
        }
        success {
            echo "✓ Pipeline succeeded!"
        }
        failure {
            echo "✗ Pipeline failed!"
            sh '''
                echo "=== Debugging Information ==="
                docker ps -a
                docker-compose ps 2>/dev/null || true
            '''
        }
    }
}
