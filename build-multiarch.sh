#!/bin/bash

# Multi-architecture Docker image builder for AI Log Analyzer
# Supports building and pushing images for amd64 and arm64 architectures

set -e

# Configuration
REGISTRY="${DOCKER_REGISTRY:-docker.io}"
USERNAME="${DOCKER_USERNAME:-paambust}"
TAG="${IMAGE_TAG:-latest}"
PLATFORMS="${PLATFORMS:-linux/amd64,linux/arm64}"

# Image names
API_IMAGE="${REGISTRY}/${USERNAME}/ai-log-analyzer-api"
WORKER_IMAGE="${REGISTRY}/${USERNAME}/ai-log-analyzer-worker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}AI Log Analyzer - Multi-Arch Builder${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if docker buildx is available
if ! command -v docker buildx &> /dev/null; then
    echo -e "${YELLOW}docker buildx not found. Installing...${NC}"
    docker buildx create --use 2>/dev/null || true
fi

# Check docker buildx version
echo -e "${GREEN}Docker Buildx Version:${NC}"
docker buildx version

# Verify Docker credentials
if [[ -z "$DOCKER_USERNAME" ]] && [[ -z "$DOCKER_PASSWORD" ]]; then
    echo -e "${YELLOW}Warning: Docker credentials not set. Make sure you're logged in to Docker Hub.${NC}"
    echo "Run: docker login"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Building Multi-Architecture Images${NC}"
echo -e "${GREEN}========================================${NC}"

# Build and push API image
echo -e "${YELLOW}Building API image: ${API_IMAGE}:${TAG}${NC}"
echo "Platforms: ${PLATFORMS}"
docker buildx build \
    --platform "${PLATFORMS}" \
    -t "${API_IMAGE}:${TAG}" \
    -t "${API_IMAGE}:latest" \
    --push \
    -f ./api/Dockerfile \
    ./api

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ API image built and pushed successfully${NC}"
else
    echo -e "${RED}✗ API image build failed${NC}"
    exit 1
fi

# Build and push Worker image
echo -e "${YELLOW}Building Worker image: ${WORKER_IMAGE}:${TAG}${NC}"
echo "Platforms: ${PLATFORMS}"
docker buildx build \
    --platform "${PLATFORMS}" \
    -t "${WORKER_IMAGE}:${TAG}" \
    -t "${WORKER_IMAGE}:latest" \
    --push \
    -f ./worker/Dockerfile \
    ./worker

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Worker image built and pushed successfully${NC}"
else
    echo -e "${RED}✗ Worker image build failed${NC}"
    exit 1
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Published Images:${NC}"
echo "  API:    ${API_IMAGE}:${TAG}"
echo "  Worker: ${WORKER_IMAGE}:${TAG}"
echo -e "${GREEN}Platforms: ${PLATFORMS}${NC}"
echo -e "${GREEN}View at: https://hub.docker.com/r/${USERNAME}${NC}"
