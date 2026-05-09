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
        DOCKER_HUB_CREDENTIALS = credentials('docker-hub-credentials')
    }

    stages {
        stage('Setup') {
            steps {
                echo "Checking dependencies..."
                sh '''
                    # Python3 and pip should already be installed in the container
                    echo "✓ Checking Python3..."
                    python3 --version
                    
                    echo "✓ Checking pip..."
                    pip3 --version || pip --version
                    
                    # Check Docker (required for this pipeline)
                    if ! command -v docker &> /dev/null; then
                        echo "❌ ERROR: Docker not found in container"
                        echo "Solution: Docker must be installed in Jenkins container"
                        exit 1
                    fi
                    echo "✓ Docker available"
                    docker --version
                    
                    # Check docker-compose
                    if command -v docker-compose &> /dev/null; then
                        echo "✓ docker-compose v1 available"
                        docker-compose --version
                    elif docker compose version &> /dev/null; then
                        echo "✓ Docker Compose v2 available"
                        docker compose version
                    else
                        echo "⚠ docker-compose not found, installing..."
                        curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" \
                            -o /usr/local/bin/docker-compose 2>/dev/null
                        chmod +x /usr/local/bin/docker-compose
                        docker-compose --version
                    fi
                    
                    echo "✓ All dependencies verified"
                '''
            }
        }

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
                    if command -v docker-compose &> /dev/null; then
                        docker-compose build --no-cache
                    else
                        docker compose build --no-cache
                    fi
                '''
            }
        }

        stage('Start Services') {
            steps {
                echo "Starting services with docker-compose..."
                sh '''
                    cd ${WORKSPACE_ROOT}
                    if command -v docker-compose &> /dev/null; then
                        docker-compose up -d
                    else
                        docker compose up -d
                    fi
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
                    COMPOSE="docker-compose"
                    if ! command -v docker-compose &> /dev/null; then
                        COMPOSE="docker compose"
                    fi
                    
                    echo "=== API Service Logs ==="
                    $COMPOSE logs api || echo "No logs available"
                    echo ""
                    echo "=== Worker Service Logs ==="
                    $COMPOSE logs worker || echo "No logs available"
                    echo ""
                    echo "=== Database Logs ==="
                    $COMPOSE logs postgres || echo "No logs available"
                '''
            }
        }

        stage('Cleanup Local Services') {
            steps {
                echo "Shutting down docker-compose services..."
                sh '''
                    cd ${WORKSPACE_ROOT}
                    COMPOSE="docker-compose"
                    if ! command -v docker-compose &> /dev/null; then
                        COMPOSE="docker compose"
                    fi
                    $COMPOSE down -v || true
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
                COMPOSE="docker-compose"
                if ! command -v docker-compose &> /dev/null; then
                    COMPOSE="docker compose"
                fi
                $COMPOSE down -v 2>/dev/null || true
                
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
                COMPOSE="docker-compose"
                if ! command -v docker-compose &> /dev/null; then
                    COMPOSE="docker compose"
                fi
                $COMPOSE ps 2>/dev/null || true
            '''
        }
    }
}
