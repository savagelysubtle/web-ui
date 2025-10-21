# Deployment Guide

**Version:** 1.0
**Last Updated:** 2025-10-21

---

## Deployment Options

### Option 1: Local Development (Recommended for Getting Started)

**Best for:** Individual developers, testing, prototyping

```bash
# 1. Clone repository
git clone https://github.com/savagelysubtle/web-ui.git
cd web-ui

# 2. Set up environment
uv python install 3.14t
uv venv --python 3.14t
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
uv sync

# 4. Install Playwright browsers
playwright install chromium --with-deps

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 6. Run application
python webui.py

# Access at: http://127.0.0.1:7788
```

---

### Option 2: Docker (Single Container)

**Best for:** Quick deployment, isolated environment

**Dockerfile** (existing):
```dockerfile
FROM python:3.14-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright browsers
RUN pip install playwright && \
    playwright install --with-deps chromium

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 7788

# Run application
CMD ["python", "webui.py", "--ip", "0.0.0.0", "--port", "7788"]
```

**Build and run:**
```bash
# Build
docker build -t browser-use-webui .

# Run
docker run -d \
  -p 7788:7788 \
  -e OPENAI_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  --name browser-use-webui \
  browser-use-webui

# Access at: http://localhost:7788
```

---

### Option 3: Docker Compose (Recommended for Production)

**Best for:** Multi-user setups, production deployments

**docker-compose.yml** (enhanced for Phase 4):
```yaml
version: '3.8'

services:
  # Main application
  webui:
    build: .
    ports:
      - "7788:7788"
      - "8000:8000"  # API server (Phase 4)
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - DATABASE_URL=postgresql://user:pass@postgres:5432/browser_use
      - REDIS_HOST=redis
      - EVENT_BUS_BACKEND=redis
    volumes:
      - ./data:/app/data  # Persistent data
      - ./logs:/app/logs  # Logs
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    networks:
      - browser-use-network

  # PostgreSQL database
  postgres:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=browser_use
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped
    networks:
      - browser-use-network

  # Redis for event bus
  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    restart: unless-stopped
    networks:
      - browser-use-network

  # VNC server for browser viewing (optional)
  vnc:
    image: dorowu/ubuntu-desktop-lxde-vnc:focal
    ports:
      - "6080:80"  # VNC web interface
    environment:
      - VNC_PASSWORD=${VNC_PASSWORD:-youvncpassword}
      - RESOLUTION=${RESOLUTION:-1920x1080x24}
    restart: unless-stopped
    networks:
      - browser-use-network

volumes:
  postgres_data:
  redis_data:

networks:
  browser-use-network:
    driver: bridge
```

**Deployment:**
```bash
# 1. Create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AIza...
VNC_PASSWORD=securepassword
EOF

# 2. Start services
docker compose up -d

# 3. Initialize database
docker compose exec webui python -m src.storage.init_db

# 4. Access services
# - Web UI: http://localhost:7788
# - API: http://localhost:8000
# - VNC: http://localhost:6080
```

---

### Option 4: Kubernetes (Enterprise Scale)

**Best for:** Large-scale deployments, high availability

**k8s/deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: browser-use-webui
  labels:
    app: browser-use-webui
spec:
  replicas: 3
  selector:
    matchLabels:
      app: browser-use-webui
  template:
    metadata:
      labels:
        app: browser-use-webui
    spec:
      containers:
      - name: webui
        image: browser-use-webui:latest
        ports:
        - containerPort: 7788
          name: http
        - containerPort: 8000
          name: api
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: browser-use-secrets
              key: database-url
        - name: REDIS_HOST
          value: redis-service
        - name: EVENT_BUS_BACKEND
          value: redis
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
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
        volumeMounts:
        - name: data
          mountPath: /app/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: browser-use-pvc

---
apiVersion: v1
kind: Service
metadata:
  name: browser-use-service
spec:
  type: LoadBalancer
  selector:
    app: browser-use-webui
  ports:
  - name: http
    port: 80
    targetPort: 7788
  - name: api
    port: 8000
    targetPort: 8000

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: browser-use-pvc
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 100Gi
```

**Deploy to Kubernetes:**
```bash
# 1. Create secrets
kubectl create secret generic browser-use-secrets \
  --from-literal=database-url="postgresql://..." \
  --from-literal=openai-api-key="sk-..." \
  --from-literal=anthropic-api-key="sk-ant-..."

# 2. Apply configurations
kubectl apply -f k8s/

# 3. Check deployment
kubectl get pods
kubectl get services

# 4. Access service
kubectl port-forward service/browser-use-service 7788:80
```

---

### Option 5: Cloud Platform Deployments

#### Railway

**railway.toml:**
```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt && playwright install chromium --with-deps"

[deploy]
startCommand = "python webui.py --ip 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

**Deploy:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create project
railway init

# Add services
railway add  # Select PostgreSQL, Redis

# Deploy
railway up
```

#### Render

**render.yaml:**
```yaml
services:
  - type: web
    name: browser-use-webui
    env: python
    buildCommand: "pip install -r requirements.txt && playwright install chromium --with-deps"
    startCommand: "python webui.py --ip 0.0.0.0 --port $PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.14
      - key: DATABASE_URL
        fromDatabase:
          name: browser-use-db
          property: connectionString
      - key: REDIS_URL
        fromService:
          type: redis
          name: browser-use-redis
          property: connectionString

databases:
  - name: browser-use-db
    databaseName: browser_use
    user: browser_use

redis:
  - name: browser-use-redis
```

**Deploy:**
1. Connect GitHub repository to Render
2. Select "Blueprint" deployment
3. Upload `render.yaml`
4. Deploy

#### Vercel (UI Only)

For deploying just the frontend (if migrating to Next.js):

**vercel.json:**
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "outputDirectory": ".next"
}
```

---

## Production Configuration

### Environment Variables (Production)

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/browser_use
REDIS_HOST=redis.production.com
REDIS_PORT=6379

# Security
ENCRYPTION_KEY=generate-with-python-secrets
JWT_SECRET=generate-with-python-secrets
SESSION_SECRET=generate-with-python-secrets
ALLOWED_ORIGINS=https://yourdomain.com

# Performance
MAX_CONCURRENT_AGENTS=50
TRACE_RETENTION_DAYS=30
ENABLE_CACHING=true

# Monitoring
SENTRY_DSN=https://...@sentry.io/...
LOG_LEVEL=warning

# Features
ENABLE_ANALYTICS=true
ENABLE_TELEMETRY=false
```

### Generate Secrets

```python
# generate_secrets.py
import secrets

print("ENCRYPTION_KEY:", secrets.token_urlsafe(32))
print("JWT_SECRET:", secrets.token_urlsafe(32))
print("SESSION_SECRET:", secrets.token_urlsafe(32))
```

### Nginx Reverse Proxy

**/etc/nginx/sites-available/browser-use:**
```nginx
upstream browser_use_app {
    server 127.0.0.1:7788;
}

upstream browser_use_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    # SSL certificates (from Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Main UI
    location / {
        proxy_pass http://browser_use_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # API endpoints
    location /api {
        proxy_pass http://browser_use_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket endpoint
    location /ws {
        proxy_pass http://browser_use_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # 24 hours
    }

    # Static files (if any)
    location /static {
        alias /var/www/browser-use/static;
        expires 30d;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/browser-use /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Monitoring & Observability

### Health Checks

**File:** `src/web_ui/api/health.py`

```python
from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health():
    """Detailed health check."""
    checks = {}

    # Database
    try:
        from src.storage import get_db
        db = get_db()
        db.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    # Redis
    try:
        from src.events.event_bus import get_event_bus
        event_bus = get_event_bus()
        if event_bus.backend == "redis":
            await event_bus.redis.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {e}"

    # Playwright
    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            await browser.close()
        checks["browser"] = "healthy"
    except Exception as e:
        checks["browser"] = f"unhealthy: {e}"

    overall_healthy = all(v == "healthy" for v in checks.values())

    return {
        "status": "healthy" if overall_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat()
    }
```

### Logging (Production)

**File:** `config/logging.yaml`

```yaml
version: 1
disable_existing_loggers: false

formatters:
  default:
    format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  json:
    (): pythonjsonlogger.jsonlogger.JsonFormatter
    format: '%(asctime)s %(name)s %(levelname)s %(message)s'

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: default
    stream: ext://sys.stdout

  file:
    class: logging.handlers.RotatingFileHandler
    level: INFO
    formatter: json
    filename: logs/browser_use.log
    maxBytes: 10485760  # 10MB
    backupCount: 5

  error_file:
    class: logging.handlers.RotatingFileHandler
    level: ERROR
    formatter: json
    filename: logs/errors.log
    maxBytes: 10485760
    backupCount: 10

loggers:
  browser_use:
    level: INFO
    handlers: [console, file, error_file]
    propagate: false

root:
  level: INFO
  handlers: [console, file]
```

### Metrics (Prometheus)

**File:** `src/web_ui/api/metrics.py`

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import APIRouter
from fastapi.responses import Response

router = APIRouter()

# Define metrics
agent_runs = Counter(
    'browser_use_agent_runs_total',
    'Total agent runs',
    ['status', 'llm_provider']
)

execution_duration = Histogram(
    'browser_use_execution_duration_seconds',
    'Execution duration in seconds',
    ['llm_provider']
)

active_sessions = Gauge(
    'browser_use_active_sessions',
    'Number of active sessions'
)

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

### Error Tracking (Sentry)

```python
# Initialize Sentry
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    integrations=[
        FastApiIntegration(),
        AsyncioIntegration(),
    ],
    traces_sample_rate=0.1,  # 10% of transactions
    environment=os.getenv("ENVIRONMENT", "production"),
)

# Sentry will automatically catch exceptions
```

---

## Backup & Recovery

### Database Backup

```bash
#!/bin/bash
# backup_db.sh

BACKUP_DIR="/backups/browser-use"
DATE=$(date +%Y%m%d_%H%M%S)

# PostgreSQL backup
pg_dump -h localhost -U browser_use browser_use | gzip > \
    "$BACKUP_DIR/db_backup_$DATE.sql.gz"

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

**Restore:**
```bash
gunzip < db_backup_20250121_120000.sql.gz | \
    psql -h localhost -U browser_use browser_use
```

### Data Backup

```bash
#!/bin/bash
# backup_data.sh

BACKUP_DIR="/backups/browser-use"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup data directory
tar -czf "$BACKUP_DIR/data_backup_$DATE.tar.gz" \
    /app/data \
    /app/logs

# Backup to S3 (optional)
aws s3 cp "$BACKUP_DIR/data_backup_$DATE.tar.gz" \
    s3://my-bucket/browser-use-backups/

echo "Data backup completed"
```

---

## Scaling Strategies

### Horizontal Scaling

```yaml
# docker-compose.scale.yml

version: '3.8'

services:
  webui:
    build: .
    deploy:
      replicas: 5  # Scale to 5 instances
      resources:
        limits:
          cpus: '2'
          memory: 4G
    # ... rest of config

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - webui
```

**nginx.conf (load balancer):**
```nginx
upstream backend {
    least_conn;  # Load balancing method
    server webui_1:7788;
    server webui_2:7788;
    server webui_3:7788;
    server webui_4:7788;
    server webui_5:7788;
}

server {
    listen 80;

    location / {
        proxy_pass http://backend;
        # ... proxy settings
    }
}
```

### Auto-Scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: browser-use-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: browser-use-webui
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## Troubleshooting

### Common Issues

**Issue:** Browser fails to start
```bash
# Solution: Install dependencies
playwright install --with-deps chromium

# Or in Docker
docker exec -it browser-use-webui playwright install --with-deps
```

**Issue:** WebSocket connection fails
```bash
# Check firewall
sudo ufw allow 8000/tcp

# Check nginx config
sudo nginx -t
```

**Issue:** High memory usage
```bash
# Limit concurrent agents
export MAX_CONCURRENT_AGENTS=5

# Monitor memory
docker stats browser-use-webui
```

---

**Last Updated:** 2025-10-21
**Next:** See [10-TESTING-STRATEGY.md](10-TESTING-STRATEGY.md) for testing guide
