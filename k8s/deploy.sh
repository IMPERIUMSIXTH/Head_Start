#!/bin/bash

# HeadStart Kubernetes Deployment Script
# This script deploys the HeadStart application to Kubernetes

set -e

echo "🚀 Starting HeadStart Kubernetes Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    print_error "Not connected to a Kubernetes cluster"
    exit 1
fi

print_status "Connected to Kubernetes cluster: $(kubectl config current-context)"

# Create namespace (optional)
kubectl create namespace headstart --dry-run=client -o yaml | kubectl apply -f -

# Apply ConfigMap and Secrets first
print_status "Applying ConfigMap and Secrets..."
kubectl apply -f configmap.yaml
kubectl apply -f secrets.yaml

# Deploy PostgreSQL
print_status "Deploying PostgreSQL..."
kubectl apply -f postgres-deployment.yaml

# Wait for PostgreSQL to be ready
print_status "Waiting for PostgreSQL to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/headstart-postgres

# Deploy Redis
print_status "Deploying Redis..."
kubectl apply -f redis-deployment.yaml

# Wait for Redis to be ready
print_status "Waiting for Redis to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/headstart-redis

# Run database migrations
print_status "Running database migrations..."
kubectl apply -f migration-job.yaml

# Wait for migration job to complete
print_status "Waiting for migration job to complete..."
kubectl wait --for=condition=complete --timeout=300s job/headstart-migration-job

# Deploy backend
print_status "Deploying backend..."
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml

# Wait for backend to be ready
print_status "Waiting for backend to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/headstart-backend

# Deploy Celery workers
print_status "Deploying Celery workers..."
kubectl apply -f celery-worker-deployment.yaml

# Deploy frontend
print_status "Deploying frontend..."
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml

# Wait for frontend to be ready
print_status "Waiting for frontend to be ready..."
kubectl wait --for=condition=available --timeout=300s deployment/headstart-frontend

# Deploy ingress (if ingress controller is available)
print_status "Deploying ingress..."
kubectl apply -f ingress.yaml

print_status "🎉 Deployment completed successfully!"

# Show status
echo ""
print_status "Deployment Status:"
kubectl get pods
kubectl get services
kubectl get ingress

echo ""
print_status "To check logs:"
echo "  Backend: kubectl logs -l app=headstart-backend"
echo "  Frontend: kubectl logs -l app=headstart-frontend"
echo "  PostgreSQL: kubectl logs -l app=headstart-postgres"
echo "  Redis: kubectl logs -l app=headstart-redis"
echo "  Celery: kubectl logs -l app=headstart-celery-worker"

echo ""
print_status "To scale deployments:"
echo "  kubectl scale deployment headstart-backend --replicas=5"
echo "  kubectl scale deployment headstart-frontend --replicas=3"

echo ""
print_status "To check ingress:"
echo "  kubectl get ingress"
echo "  kubectl describe ingress headstart-ingress"
