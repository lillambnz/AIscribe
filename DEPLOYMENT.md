# Deployment Guide

This guide covers deploying AIscribe to production in Australian cloud regions.

## Production Requirements

### Infrastructure

- **Cloud Provider**: GCP (australia-southeast1) or Azure (Australia East)
- **Compute**:
  - Backend: 2+ vCPUs, 4GB+ RAM (8GB+ recommended for Whisper)
  - Frontend: 1 vCPU, 1GB RAM
- **Database**: PostgreSQL 15+, 2+ vCPUs, 4GB+ RAM
- **Storage**: S3-compatible object storage (GCS/Azure Blob)
- **SSL/TLS**: Valid certificate (Let's Encrypt or commercial)

### Compliance Checklist

- [ ] All services deployed in Australia
- [ ] Data encryption at rest (AES-256)
- [ ] TLS 1.3 for all connections
- [ ] Audit logging enabled
- [ ] Backup strategy implemented
- [ ] Retention policies configured
- [ ] Access controls (RBAC) configured
- [ ] SSO integration tested
- [ ] PHI protection verified
- [ ] Disaster recovery plan documented

## Docker Deployment

### Production Docker Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.prod
    environment:
      DATABASE_URL: postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      SECRET_KEY: ${SECRET_KEY}
      CORS_ORIGINS: ${CORS_ORIGINS}
      # ... other production env vars
    restart: always
    depends_on:
      postgres:
        condition: service_healthy

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    environment:
      NEXT_PUBLIC_API_URL: ${API_URL}
      NEXT_PUBLIC_WS_URL: ${WS_URL}
    restart: always
    depends_on:
      - backend

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    restart: always
    depends_on:
      - backend
      - frontend

volumes:
  postgres_data:
```

### Deploy

```bash
# Build images
docker-compose -f docker-compose.prod.yml build

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
```

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster in AU region
- kubectl configured
- Helm 3+ installed

### Create Namespace

```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: aiscribe
```

### Database (Cloud SQL / Azure Database)

For GCP Cloud SQL:

```yaml
# cloudsql-secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloudsql-db-credentials
  namespace: aiscribe
type: Opaque
data:
  username: <base64-encoded>
  password: <base64-encoded>
```

### Backend Deployment

```yaml
# backend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiscribe-backend
  namespace: aiscribe
spec:
  replicas: 3
  selector:
    matchLabels:
      app: aiscribe-backend
  template:
    metadata:
      labels:
        app: aiscribe-backend
    spec:
      containers:
      - name: backend
        image: gcr.io/your-project/aiscribe-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: aiscribe-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: aiscribe-secrets
              key: secret-key
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/db
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
```

### Frontend Deployment

```yaml
# frontend-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aiscribe-frontend
  namespace: aiscribe
spec:
  replicas: 2
  selector:
    matchLabels:
      app: aiscribe-frontend
  template:
    metadata:
      labels:
        app: aiscribe-frontend
    spec:
      containers:
      - name: frontend
        image: gcr.io/your-project/aiscribe-frontend:latest
        ports:
        - containerPort: 3000
        env:
        - name: NEXT_PUBLIC_API_URL
          value: "https://api.yourdomain.com.au"
        - name: NEXT_PUBLIC_WS_URL
          value: "wss://api.yourdomain.com.au"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1"
```

### Ingress with TLS

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: aiscribe-ingress
  namespace: aiscribe
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/websocket-services: "aiscribe-backend"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - yourdomain.com.au
    - api.yourdomain.com.au
    secretName: aiscribe-tls
  rules:
  - host: yourdomain.com.au
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aiscribe-frontend
            port:
              number: 3000
  - host: api.yourdomain.com.au
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: aiscribe-backend
            port:
              number: 8000
```

### Deploy to Kubernetes

```bash
# Apply configurations
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml
kubectl apply -f backend-deployment.yaml
kubectl apply -f backend-service.yaml
kubectl apply -f frontend-deployment.yaml
kubectl apply -f frontend-service.yaml
kubectl apply -f ingress.yaml

# Check status
kubectl get pods -n aiscribe
kubectl get ingress -n aiscribe

# View logs
kubectl logs -f deployment/aiscribe-backend -n aiscribe
```

## Environment Variables (Production)

### Backend

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db

# Security
SECRET_KEY=<generate-strong-key-min-32-chars>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ASR
AZURE_SPEECH_KEY=<your-key>
AZURE_SPEECH_REGION=australiaeast
WHISPER_MODEL=medium
WHISPER_DEVICE=cpu
WHISPER_COMPUTE_TYPE=int8

# Storage (GCS example)
STORAGE_BACKEND=gcs
GCS_BUCKET_NAME=aiscribe-audio-prod
GCS_CREDENTIALS_PATH=/secrets/gcs-key.json

# Compliance
AU_DATA_RESIDENCY=true
ENCRYPTION_KEY_ID=production-kms-key
AUDIO_RETENTION_DAYS=90
TRANSCRIPT_RETENTION_DAYS=2555

# OAuth (Microsoft Entra)
OAUTH_ENABLED=true
OAUTH_CLIENT_ID=<your-client-id>
OAUTH_CLIENT_SECRET=<your-client-secret>
OAUTH_TENANT_ID=<your-tenant-id>
OAUTH_AUTHORITY=https://login.microsoftonline.com/<tenant-id>

# CORS
CORS_ORIGINS=["https://yourdomain.com.au"]

# Logging
LOG_LEVEL=INFO
SENTRY_DSN=<your-sentry-dsn>
```

## Monitoring & Logging

### Application Monitoring

Use Sentry for error tracking:

```python
# In backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    integrations=[FastApiIntegration()],
    environment="production",
)
```

### Prometheus Metrics

Add Prometheus exporter to backend:

```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

@app.on_event("startup")
async def startup():
    Instrumentator().instrument(app).expose(app)
```

### Log Aggregation

Use structured logging with Cloud Logging (GCP) or Azure Monitor.

## Backup Strategy

### Database Backups

```bash
# Automated daily backups
0 2 * * * pg_dump aiscribe | gzip > /backups/aiscribe-$(date +\%Y\%m\%d).sql.gz

# Retention: keep 30 days
find /backups -name "aiscribe-*.sql.gz" -mtime +30 -delete
```

### Object Storage

Enable versioning and lifecycle policies in GCS/Azure Blob.

## Security Hardening

1. **Network Security**:
   - Use VPC/VNET
   - Restrict database to private subnet
   - Use Cloud Armor/WAF

2. **Secrets Management**:
   - Use Secret Manager (GCP) or Key Vault (Azure)
   - Rotate secrets regularly
   - Never commit secrets to git

3. **Access Control**:
   - Enable MFA for all admin accounts
   - Use service accounts with minimal permissions
   - Implement RBAC

4. **Audit**:
   - Enable Cloud Audit Logs
   - Monitor unusual access patterns
   - Set up alerts for security events

## Performance Optimization

1. **Whisper Optimization**:
   - Use GPU (T4/L4) for faster-whisper
   - Use int8 quantization for CPU
   - Cache models on persistent disk

2. **Database**:
   - Enable connection pooling
   - Add indexes on frequently queried fields
   - Use read replicas for analytics

3. **Caching**:
   - Use Redis for session storage
   - Cache frequently accessed transcripts
   - Implement CDN for static assets

## Disaster Recovery

1. **Database**:
   - Daily automated backups
   - Cross-region replication
   - Test restore procedure monthly

2. **Application**:
   - Multi-AZ deployment
   - Automated failover
   - Runbook for common incidents

3. **Data**:
   - Object storage versioning
   - Cross-region bucket replication
   - Documented recovery procedures

## Cost Optimization

1. **Compute**:
   - Use auto-scaling
   - Right-size instances
   - Use spot/preemptible instances for non-critical workloads

2. **Storage**:
   - Implement lifecycle policies
   - Use coldline/archive storage for old audio
   - Compress audio files

3. **Monitoring**:
   - Set budget alerts
   - Review resource utilization monthly
   - Eliminate unused resources
