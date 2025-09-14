# HeadStart Kubernetes Deployment

This directory contains Kubernetes manifests for deploying the HeadStart application to a Kubernetes cluster.

## 📋 Prerequisites

- Kubernetes cluster (v1.19+)
- kubectl configured to access your cluster
- NGINX Ingress Controller (for ingress functionality)
- cert-manager (for TLS certificates, optional)
- Storage class for persistent volumes

## 🚀 Quick Start

### 1. Clone and navigate to the project
```bash
git clone <repository-url>
cd headstart/k8s
```

### 2. Update configuration
Edit the following files with your specific values:
- `configmap.yaml`: Update environment variables
- `secrets.yaml`: Update sensitive values (passwords, API keys)
- `ingress.yaml`: Update domain name

### 3. Deploy the application
```bash
# Make the deployment script executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

### 4. Test the deployment
```bash
# Make the test script executable
chmod +x test-deployment.sh

# Run comprehensive tests
./test-deployment.sh
```

## 📁 Manifest Files

| File | Description |
|------|-------------|
| `configmap.yaml` | Application configuration (non-sensitive) |
| `secrets.yaml` | Sensitive configuration (passwords, API keys) |
| `postgres-deployment.yaml` | PostgreSQL database deployment and service |
| `redis-deployment.yaml` | Redis cache deployment and service |
| `backend-deployment.yaml` | FastAPI backend deployment |
| `backend-service.yaml` | Backend service definition |
| `frontend-deployment.yaml` | Next.js frontend deployment |
| `frontend-service.yaml` | Frontend service definition |
| `celery-worker-deployment.yaml` | Celery worker deployment |
| `ingress.yaml` | Ingress configuration for external access |
| `migration-job.yaml` | Database migration job |
| `deploy.sh` | Automated deployment script |
| `test-deployment.sh` | Comprehensive testing script |

## 🔧 Configuration

### Environment Variables

Update `configmap.yaml` with your environment-specific values:

```yaml
data:
  POSTGRES_DB: "your_database_name"
  POSTGRES_USER: "your_database_user"
  REDIS_URL: "redis://redis-service:6379/0"
  NEXT_PUBLIC_API_URL: "http://headstart-backend-service:8000"
  ENVIRONMENT: "production"
```

### Secrets

Update `secrets.yaml` with your actual secrets:

```yaml
stringData:
  POSTGRES_PASSWORD: "your_actual_password"
  JWT_SECRET: "your_jwt_secret"
  OPENAI_API_KEY: "your_openai_key"
```

### Ingress

Update `ingress.yaml` with your domain:

```yaml
spec:
  rules:
  - host: your-domain.com
```

## 🧪 Testing

The `test-deployment.sh` script performs comprehensive testing:

- Pod status verification
- Service availability
- Deployment health
- Persistent volume status
- Ingress configuration
- Application endpoint testing
- Database connectivity
- Redis connectivity
- Error log analysis

## 📊 Monitoring

### Check pod status
```bash
kubectl get pods
```

### View logs
```bash
# Backend logs
kubectl logs -l app=headstart-backend

# Frontend logs
kubectl logs -l app=headstart-frontend

# Database logs
kubectl logs -l app=headstart-postgres
```

### Monitor resources
```bash
kubectl top pods
kubectl top nodes
```

## 🔄 Scaling

### Scale backend
```bash
kubectl scale deployment headstart-backend --replicas=5
```

### Scale frontend
```bash
kubectl scale deployment headstart-frontend --replicas=3
```

### Scale workers
```bash
kubectl scale deployment headstart-celery-worker --replicas=4
```

## 🔧 Troubleshooting

### Common Issues

1. **Pods not starting**
   ```bash
   kubectl describe pod <pod-name>
   kubectl logs <pod-name>
   ```

2. **Service not accessible**
   ```bash
   kubectl get services
   kubectl describe service <service-name>
   ```

3. **Ingress not working**
   ```bash
   kubectl get ingress
   kubectl describe ingress headstart-ingress
   ```

4. **Database connection issues**
   ```bash
   kubectl exec -it <postgres-pod> -- psql -U headstart_user -d headstart
   ```

### Debug commands
```bash
# Check cluster events
kubectl get events --sort-by=.metadata.creationTimestamp

# Check resource usage
kubectl describe nodes

# Check persistent volumes
kubectl get pv,pvc
```

## 🔒 Security Considerations

1. **Secrets Management**: Use Kubernetes secrets or external secret management
2. **Network Policies**: Implement network policies for pod communication
3. **RBAC**: Configure proper role-based access control
4. **TLS**: Enable HTTPS with cert-manager
5. **Image Security**: Scan container images for vulnerabilities

## 📈 Performance Tuning

### Resource Limits
Update resource requests and limits in deployment files based on your needs:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "512Mi"
    cpu: "500m"
```

### Horizontal Pod Autoscaling
```bash
kubectl autoscale deployment headstart-backend --cpu-percent=70 --min=3 --max=10
```

## 🔄 Updates and Rollbacks

### Rolling updates
```bash
kubectl set image deployment/headstart-backend backend=headstart/backend:v2.0.0
```

### Rollback
```bash
kubectl rollout undo deployment/headstart-backend
```

### Check rollout status
```bash
kubectl rollout status deployment/headstart-backend
```

## 🗑️ Cleanup

To remove the entire deployment:

```bash
kubectl delete -f .
```

Or remove specific components:

```bash
kubectl delete deployment,svc,ingress,pvc,configmap,secret -l app=headstart
```

## 📞 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Kubernetes logs and events
3. Consult the main project documentation
4. Check Kubernetes community resources

## 📝 Notes

- All manifests use the `default` namespace
- Persistent volumes require a storage class to be available
- Ingress assumes NGINX ingress controller is installed
- Database migrations run automatically during deployment
- Health checks are configured for all services
- Resource limits are set conservatively and can be adjusted
