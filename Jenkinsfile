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
                    
                    # Determine which compose command to use
                    COMPOSE="docker-compose"
                    if ! command -v docker-compose &> /dev/null; then
                        COMPOSE="docker compose"
                    fi
                    
                    # Enhanced wait logic using Python (more reliable than curl)
                    echo "Waiting for services to reach healthy state..."
                    python3 << 'EOF'
import socket
import time
import sys

def check_port(host, port, timeout=2):
    """Check if a port is open"""
    try:
        socket.create_connection((host, port), timeout=timeout)
        return True
    except (socket.timeout, socket.error):
        return False

# Wait for API to be ready
max_retries = 30
retry = 0
while retry < max_retries:
    if check_port('api-service', 8000):
        print("✓ API service is ready on port 8000!")
        break
    retry += 1
    print(f"  Attempt {retry}/{max_retries} - Waiting for API service...")
    time.sleep(2)
else:
    print("✗ API service failed to start within timeout")
    sys.exit(1)

# Wait for database to be ready
retry = 0
while retry < max_retries:
    if check_port('postgres', 5432):
        print("✓ Database service is ready on port 5432!")
        break
    retry += 1
    print(f"  Attempt {retry}/{max_retries} - Waiting for database...")
    time.sleep(2)
else:
    print("✗ Database service failed to start within timeout")
    sys.exit(1)

print("✓ All services are ready!")
EOF
                    
                    # Run integration tests
                    echo "Running integration tests..."
                    API_URL="http://api-service:8000" python3 tests/test_api.py
                    echo "✓ All tests passed!"
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
