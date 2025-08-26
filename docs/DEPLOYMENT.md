# Deployment Guide

## Production Deployment

### Docker Deployment

#### Single Instance
```bash
# Build production image
docker build -t youtube-transcribe:production .

# Run with production configuration
docker run -d \
  --name youtube-transcribe \
  -p 8000:8000 \
  -v ./credentials:/app/credentials \
  -v ./data:/app/data \
  -e MODE=api \
  -e GCS_BUCKET_NAME=your-production-bucket \
  -e VERTEX_PROJECT_ID=your-project-id \
  -e VERTEX_AI_MODEL=gemini-2.0-flash \
  youtube-transcribe:production
```

#### Docker Compose Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  transcribe:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - MODE=api
      - GCS_BUCKET_NAME=${GCS_BUCKET_NAME}
      - VERTEX_PROJECT_ID=${VERTEX_PROJECT_ID}
      - VERTEX_AI_MODEL=gemini-2.0-flash
      - API_HOST=0.0.0.0
      - API_PORT=8000
      - SYNC_SIZE_LIMIT_MB=10
      - MAX_CONCURRENT_JOBS=5
    volumes:
      - ./credentials:/app/credentials:ro
      - transcribe_data:/app/data
      - transcribe_temp:/app/temp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - transcribe
    restart: unless-stopped

volumes:
  transcribe_data:
  transcribe_temp:
```

### Kubernetes Deployment

#### ConfigMap
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: transcribe-config
data:
  MODE: "api"
  GCS_BUCKET_NAME: "your-production-bucket"
  VERTEX_PROJECT_ID: "your-project-id"
  VERTEX_AI_MODEL: "gemini-2.0-flash"
  API_HOST: "0.0.0.0"
  API_PORT: "8000"
  LANGUAGE_CODE: "hu-HU"
  SYNC_SIZE_LIMIT_MB: "10"
  MAX_CONCURRENT_JOBS: "5"
```

#### Secret for Service Account
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: gcp-service-account
type: Opaque
data:
  service-account.json: <base64-encoded-service-account-key>
```

#### Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: youtube-transcribe
  labels:
    app: youtube-transcribe
spec:
  replicas: 3
  selector:
    matchLabels:
      app: youtube-transcribe
  template:
    metadata:
      labels:
        app: youtube-transcribe
    spec:
      containers:
      - name: transcribe
        image: youtube-transcribe:production
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: transcribe-config
        env:
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: "/app/credentials/service-account.json"
        volumeMounts:
        - name: credentials
          mountPath: /app/credentials
          readOnly: true
        - name: data-volume
          mountPath: /app/data
        - name: temp-volume
          mountPath: /app/temp
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
      volumes:
      - name: credentials
        secret:
          secretName: gcp-service-account
      - name: data-volume
        persistentVolumeClaim:
          claimName: transcribe-data-pvc
      - name: temp-volume
        emptyDir: {}
```

#### Service
```yaml
apiVersion: v1
kind: Service
metadata:
  name: youtube-transcribe-service
spec:
  selector:
    app: youtube-transcribe
  ports:
    - protocol: TCP
      port: 80
      targetPort: 8000
  type: LoadBalancer
```

#### Ingress
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: youtube-transcribe-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/client-max-body-size: "50m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
spec:
  tls:
  - hosts:
    - transcribe.yourdomain.com
    secretName: transcribe-tls
  rules:
  - host: transcribe.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: youtube-transcribe-service
            port:
              number: 80
```

## Cloud Provider Deployments

### Google Cloud Run

#### Deploy Script
```bash
#!/bin/bash
set -e

PROJECT_ID="your-project-id"
SERVICE_NAME="youtube-transcribe"
REGION="us-central1"
IMAGE="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# Build and push image
docker build -t $IMAGE .
docker push $IMAGE

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars="MODE=api,GCS_BUCKET_NAME=your-bucket,VERTEX_PROJECT_ID=$PROJECT_ID,VERTEX_AI_MODEL=gemini-2.0-flash" \
  --memory 4Gi \
  --cpu 2 \
  --timeout 900 \
  --concurrency 10 \
  --max-instances 100
```

### AWS ECS

#### Task Definition
```json
{
  "family": "youtube-transcribe",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::ACCOUNT:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::ACCOUNT:role/transcribeTaskRole",
  "containerDefinitions": [
    {
      "name": "transcribe",
      "image": "your-account.dkr.ecr.region.amazonaws.com/youtube-transcribe:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "MODE", "value": "api"},
        {"name": "GCS_BUCKET_NAME", "value": "your-bucket"},
        {"name": "VERTEX_PROJECT_ID", "value": "your-project-id"},
        {"name": "VERTEX_AI_MODEL", "value": "gemini-2.0-flash"}
      ],
      "secrets": [
        {
          "name": "GOOGLE_APPLICATION_CREDENTIALS_JSON",
          "valueFrom": "arn:aws:secretsmanager:region:account:secret:gcp-service-account"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/youtube-transcribe",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "healthCheck": {
        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
        "interval": 30,
        "timeout": 5,
        "retries": 3
      }
    }
  ]
}
```

### Azure Container Instances

```bash
az container create \
  --resource-group myResourceGroup \
  --name youtube-transcribe \
  --image myregistry.azurecr.io/youtube-transcribe:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 \
  --environment-variables \
    MODE=api \
    GCS_BUCKET_NAME=your-bucket \
    VERTEX_PROJECT_ID=your-project-id \
    VERTEX_AI_MODEL=gemini-2.0-flash \
  --secure-environment-variables \
    GOOGLE_APPLICATION_CREDENTIALS_JSON=@service-account.json
```

## Load Balancing & Scaling

### Nginx Configuration
```nginx
upstream transcribe_backend {
    least_conn;
    server transcribe1:8000 max_fails=3 fail_timeout=30s;
    server transcribe2:8000 max_fails=3 fail_timeout=30s;
    server transcribe3:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name transcribe.yourdomain.com;
    
    client_max_body_size 50M;
    proxy_read_timeout 300s;
    proxy_connect_timeout 60s;
    proxy_send_timeout 300s;
    
    location / {
        proxy_pass http://transcribe_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /health {
        access_log off;
        proxy_pass http://transcribe_backend;
        proxy_set_header Host $host;
    }
}
```

### Auto-scaling with Docker Swarm
```yaml
version: '3.8'
services:
  transcribe:
    image: youtube-transcribe:production
    ports:
      - "8000:8000"
    environment:
      - MODE=api
      - VERTEX_AI_MODEL=gemini-2.0-flash
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
    networks:
      - transcribe_network

networks:
  transcribe_network:
    driver: overlay
```

## Monitoring & Observability

### Prometheus Metrics
```python
# Add to api.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import Response

# Metrics
job_requests = Counter('transcribe_jobs_total', 'Total transcription jobs', ['status'])
job_duration = Histogram('transcribe_job_duration_seconds', 'Job processing time')
active_jobs = Gauge('transcribe_active_jobs', 'Currently active jobs')
vertex_ai_model_usage = Counter('vertex_ai_model_requests_total', 'Vertex AI model usage', ['model'])

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Health Check Endpoint Enhancement
```python
@app.get("/health/detailed")
async def detailed_health():
    health_data = {
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": settings.mode,
        "services": {
            "google_speech": await check_speech_api(),
            "google_storage": await check_gcs_access(),
            "vertex_ai": await check_vertex_ai(),
        },
        "resources": {
            "memory_usage": get_memory_usage(),
            "disk_usage": get_disk_usage(),
            "active_jobs": len(jobs)
        }
    }
    return health_data
```

### Logging Configuration
```yaml
# docker-compose.prod.yml logging
version: '3.8'
services:
  transcribe:
    # ... other config
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"
    # Or use centralized logging
    logging:
      driver: "gelf"
      options:
        gelf-address: "udp://logstash:12201"
        tag: "youtube-transcribe"
```

## Security Considerations

### Production Security Checklist

- [ ] **Secrets Management**: Use proper secret management (K8s secrets, AWS Secrets Manager, etc.)
- [ ] **TLS/SSL**: Enable HTTPS with valid certificates
- [ ] **Authentication**: Implement API authentication if needed
- [ ] **Rate Limiting**: Implement rate limiting to prevent abuse
- [ ] **Network Security**: Restrict network access using firewalls/security groups
- [ ] **Container Security**: Scan images for vulnerabilities
- [ ] **Resource Limits**: Set appropriate resource limits
- [ ] **Monitoring**: Set up comprehensive monitoring and alerting
- [ ] **Backup**: Implement data backup strategies
- [ ] **Updates**: Establish update/patching procedures

### Environment Variables Security
```bash
# Never commit these to version control
export GCS_BUCKET_NAME="production-bucket"
export VERTEX_PROJECT_ID="production-project-id"
export GOOGLE_APPLICATION_CREDENTIALS="/secure/path/service-account.json"
export VERTEX_AI_MODEL="gemini-2.0-flash"
```

### API Rate Limiting
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.post("/v1/transcribe")
@limiter.limit("10/minute")
async def create_transcription(request: Request, transcribe_request: TranscribeRequest):
    # Implementation
```

This deployment guide covers production-ready deployment scenarios with proper security, monitoring, and scaling considerations.