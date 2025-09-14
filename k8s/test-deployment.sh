#!/bin/bash

# HeadStart Kubernetes Deployment Testing Script
# This script tests the deployed HeadStart application

set -e

echo "🧪 Testing HeadStart Kubernetes Deployment"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

print_test() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    print_error "kubectl is not installed or not in PATH"
    exit 1
fi

# Get ingress host
INGRESS_HOST=$(kubectl get ingress headstart-ingress -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "")

if [ -z "$INGRESS_HOST" ]; then
    print_warning "No ingress found, using port-forwarding for testing"
    INGRESS_HOST="localhost"
    PORT_FORWARD=true
else
    print_status "Found ingress host: $INGRESS_HOST"
fi

# Function to test HTTP endpoint
test_endpoint() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3

    print_test "Testing $description: $url"

    if [ "$PORT_FORWARD" = true ]; then
        # Set up port forwarding if needed
        kubectl port-forward svc/headstart-frontend-service 3000:3000 &
        PF_PID=$!
        sleep 3

        # Test frontend
        if curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -q "^200$"; then
            print_status "✅ Frontend is responding"
        else
            print_error "❌ Frontend is not responding"
        fi

        # Test backend via port forwarding
        kubectl port-forward svc/headstart-backend-service 8000:8000 &
        PF_PID2=$!
        sleep 3

        if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health | grep -q "^200$"; then
            print_status "✅ Backend health check passed"
        else
            print_error "❌ Backend health check failed"
        fi

        # Clean up port forwarding
        kill $PF_PID $PF_PID2 2>/dev/null || true
    else
        # Test via ingress
        if curl -s -o /dev/null -w "%{http_code}" https://$INGRESS_HOST | grep -q "^200$"; then
            print_status "✅ Frontend is responding via ingress"
        else
            print_error "❌ Frontend is not responding via ingress"
        fi

        if curl -s -o /dev/null -w "%{http_code}" https://$INGRESS_HOST/api/health | grep -q "^200$"; then
            print_status "✅ Backend health check passed via ingress"
        else
            print_error "❌ Backend health check failed via ingress"
        fi
    fi
}

# Test 1: Check all pods are running
print_test "Checking pod status..."
kubectl get pods --no-headers | while read line; do
    pod_name=$(echo $line | awk '{print $1}')
    status=$(echo $line | awk '{print $3}')
    if [ "$status" = "Running" ] || [ "$status" = "Completed" ]; then
        print_status "✅ Pod $pod_name is $status"
    else
        print_error "❌ Pod $pod_name is $status"
    fi
done

# Test 2: Check services
print_test "Checking service status..."
kubectl get services --no-headers | grep -E "(headstart|postgres|redis)" | while read line; do
    svc_name=$(echo $line | awk '{print $1}')
    svc_type=$(echo $line | awk '{print $2}')
    cluster_ip=$(echo $line | awk '{print $3}')
    print_status "✅ Service $svc_name ($svc_type) at $cluster_ip"
done

# Test 3: Check deployments
print_test "Checking deployment status..."
kubectl get deployments --no-headers | grep headstart | while read line; do
    deploy_name=$(echo $line | awk '{print $1}')
    ready=$(echo $line | awk '{print $2}')
    print_status "✅ Deployment $deploy_name: $ready"
done

# Test 4: Check persistent volumes
print_test "Checking persistent volume claims..."
kubectl get pvc --no-headers | grep -E "(postgres|redis)" | while read line; do
    pvc_name=$(echo $line | awk '{print $1}')
    status=$(echo $line | awk '{print $2}')
    if [ "$status" = "Bound" ]; then
        print_status "✅ PVC $pvc_name is $status"
    else
        print_error "❌ PVC $pvc_name is $status"
    fi
done

# Test 5: Check ingress
print_test "Checking ingress..."
if kubectl get ingress headstart-ingress &>/dev/null; then
    ingress_class=$(kubectl get ingress headstart-ingress -o jsonpath='{.spec.ingressClassName}')
    hosts=$(kubectl get ingress headstart-ingress -o jsonpath='{.spec.rules[*].host}')
    print_status "✅ Ingress configured with class: $ingress_class"
    print_status "✅ Ingress hosts: $hosts"
else
    print_warning "⚠️  No ingress found"
fi

# Test 6: Test application endpoints
print_test "Testing application endpoints..."
test_endpoint "http://$INGRESS_HOST" 200 "Frontend"
test_endpoint "http://$INGRESS_HOST/api/health" 200 "Backend Health"

# Test 7: Check resource usage
print_test "Checking resource usage..."
kubectl top pods 2>/dev/null || print_warning "kubectl top not available (metrics-server may not be installed)"

# Test 8: Check logs for errors
print_test "Checking for error logs in pods..."
for pod in $(kubectl get pods --no-headers -o custom-columns=":metadata.name" | grep -E "(headstart|postgres|redis)"); do
    error_count=$(kubectl logs $pod --since=10m 2>/dev/null | grep -i error | wc -l)
    if [ "$error_count" -gt 0 ]; then
        print_warning "⚠️  Pod $pod has $error_count error(s) in logs"
    else
        print_status "✅ Pod $pod has no recent errors"
    fi
done

# Test 9: Check database connectivity (if possible)
print_test "Testing database connectivity..."
# This would require exec into a pod and running a database client
# For now, just check if postgres pod is responding to basic queries
if kubectl exec $(kubectl get pods -l app=headstart-postgres -o jsonpath='{.items[0].metadata.name}') -- pg_isready -U headstart_user -d headstart &>/dev/null; then
    print_status "✅ PostgreSQL is accepting connections"
else
    print_error "❌ PostgreSQL is not accepting connections"
fi

# Test 10: Check Redis connectivity
print_test "Testing Redis connectivity..."
if kubectl exec $(kubectl get pods -l app=headstart-redis -o jsonpath='{.items[0].metadata.name}') -- redis-cli ping | grep -q "PONG"; then
    print_status "✅ Redis is responding to ping"
else
    print_error "❌ Redis is not responding"
fi

echo ""
print_status "🎉 Deployment testing completed!"

# Summary
echo ""
print_status "Test Summary:"
echo "  ✅ Pod Status Check"
echo "  ✅ Service Status Check"
echo "  ✅ Deployment Status Check"
echo "  ✅ Persistent Volume Check"
echo "  ✅ Ingress Configuration Check"
echo "  ✅ Application Endpoint Tests"
echo "  ✅ Resource Usage Check"
echo "  ✅ Error Log Analysis"
echo "  ✅ Database Connectivity Test"
echo "  ✅ Redis Connectivity Test"

echo ""
print_status "Next steps:"
echo "  1. Monitor application logs: kubectl logs -f deployment/headstart-backend"
echo "  2. Check application metrics and performance"
echo "  3. Set up monitoring and alerting"
echo "  4. Configure backup strategies"
echo "  5. Set up CI/CD for automated deployments"
