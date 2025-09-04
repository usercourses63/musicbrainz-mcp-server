# Deployment Guide

This guide covers various deployment options for the MusicBrainz MCP Server.

## Prerequisites

- Python 3.8+ (for local deployment)
- Docker (for containerized deployment)
- Valid MusicBrainz user agent string

## Local Deployment

### 1. Basic Local Setup

```bash
# Clone repository
git clone <repository-url>
cd MusicBrainzMcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Set required environment variables
export MUSICBRAINZ_USER_AGENT="YourApp/1.0.0 (contact@example.com)"

# Run server
python -m musicbrainz_mcp.main
```

### 2. Production Local Setup

```bash
# Install with production dependencies
pip install -e ".[prod]"

# Create production config
cat > config.json << EOF
{
  "api": {
    "user_agent": "ProductionApp/1.0.0 (admin@company.com)",
    "rate_limit": 0.8,
    "timeout": 15.0
  },
  "cache": {
    "enabled": true,
    "default_ttl": 600,
    "max_size": 5000
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": false,
    "log_level": "WARNING"
  }
}
EOF

# Run with production settings
python -m musicbrainz_mcp.main
```

## Docker Deployment

### 1. Basic Docker

```bash
# Build image
docker build -t musicbrainz-mcp .

# Run container
docker run -d \
  --name musicbrainz-mcp \
  -p 8000:8000 \
  -e MUSICBRAINZ_USER_AGENT="DockerApp/1.0.0" \
  musicbrainz-mcp
```

### 2. Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Docker with Custom Config

```bash
# Create config file
cat > docker-config.json << EOF
{
  "api": {
    "user_agent": "DockerApp/1.0.0 (docker@example.com)",
    "rate_limit": 1.0
  },
  "cache": {
    "enabled": true,
    "default_ttl": 300
  }
}
EOF

# Run with mounted config
docker run -d \
  --name musicbrainz-mcp \
  -p 8000:8000 \
  -v $(pwd)/docker-config.json:/app/config.json:ro \
  musicbrainz-mcp
```

## Cloud Deployment

### 1. Heroku Deployment

Create `Procfile`:
```
web: python -m musicbrainz_mcp.main --port $PORT
```

Deploy:
```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-musicbrainz-mcp

# Set environment variables
heroku config:set MUSICBRAINZ_USER_AGENT="HerokuApp/1.0.0"

# Deploy
git push heroku main
```

### 2. AWS Lambda Deployment

Create `lambda_handler.py`:
```python
import json
from mangum import Mangum
from musicbrainz_mcp.main import app

handler = Mangum(app)

def lambda_handler(event, context):
    return handler(event, context)
```

Package and deploy:
```bash
# Install dependencies
pip install mangum

# Create deployment package
zip -r deployment.zip . -x "tests/*" "docs/*" "*.git*"

# Deploy using AWS CLI or console
aws lambda create-function \
  --function-name musicbrainz-mcp \
  --runtime python3.11 \
  --role arn:aws:iam::account:role/lambda-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://deployment.zip
```

### 3. Google Cloud Run

Create `cloudbuild.yaml`:
```yaml
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/musicbrainz-mcp', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/musicbrainz-mcp']
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'musicbrainz-mcp'
      - '--image'
      - 'gcr.io/$PROJECT_ID/musicbrainz-mcp'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
```

Deploy:
```bash
gcloud builds submit --config cloudbuild.yaml
```

### 4. Azure Container Instances

```bash
# Create resource group
az group create --name musicbrainz-rg --location eastus

# Deploy container
az container create \
  --resource-group musicbrainz-rg \
  --name musicbrainz-mcp \
  --image musicbrainz-mcp:latest \
  --dns-name-label musicbrainz-mcp \
  --ports 8000 \
  --environment-variables \
    MUSICBRAINZ_USER_AGENT="AzureApp/1.0.0"
```

## Kubernetes Deployment

### 1. Basic Kubernetes Deployment

Create `k8s-deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: musicbrainz-mcp
spec:
  replicas: 3
  selector:
    matchLabels:
      app: musicbrainz-mcp
  template:
    metadata:
      labels:
        app: musicbrainz-mcp
    spec:
      containers:
      - name: musicbrainz-mcp
        image: musicbrainz-mcp:latest
        ports:
        - containerPort: 8000
        env:
        - name: MUSICBRAINZ_USER_AGENT
          value: "K8sApp/1.0.0"
        - name: CACHE_ENABLED
          value: "true"
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
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
---
apiVersion: v1
kind: Service
metadata:
  name: musicbrainz-mcp-service
spec:
  selector:
    app: musicbrainz-mcp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

Deploy:
```bash
kubectl apply -f k8s-deployment.yaml
```

### 2. Kubernetes with ConfigMap

Create `k8s-configmap.yaml`:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: musicbrainz-config
data:
  config.json: |
    {
      "api": {
        "user_agent": "K8sApp/1.0.0",
        "rate_limit": 1.0,
        "timeout": 10.0
      },
      "cache": {
        "enabled": true,
        "default_ttl": 300
      },
      "server": {
        "debug": false,
        "log_level": "INFO"
      }
    }
```

Update deployment to use ConfigMap:
```yaml
# Add to deployment spec.template.spec.containers[0]
volumeMounts:
- name: config-volume
  mountPath: /app/config.json
  subPath: config.json
volumes:
- name: config-volume
  configMap:
    name: musicbrainz-config
```

## Systemd Service

### 1. Create Service File

Create `/etc/systemd/system/musicbrainz-mcp.service`:
```ini
[Unit]
Description=MusicBrainz MCP Server
After=network.target

[Service]
Type=simple
User=musicbrainz
Group=musicbrainz
WorkingDirectory=/opt/musicbrainz-mcp
Environment=MUSICBRAINZ_USER_AGENT=SystemdApp/1.0.0
Environment=CACHE_ENABLED=true
Environment=DEBUG=false
ExecStart=/opt/musicbrainz-mcp/venv/bin/python -m musicbrainz_mcp.main
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/musicbrainz-mcp

[Install]
WantedBy=multi-user.target
```

### 2. Install and Start Service

```bash
# Create user
sudo useradd --system --home /opt/musicbrainz-mcp musicbrainz

# Install application
sudo mkdir -p /opt/musicbrainz-mcp
sudo chown musicbrainz:musicbrainz /opt/musicbrainz-mcp
sudo -u musicbrainz git clone <repo> /opt/musicbrainz-mcp
cd /opt/musicbrainz-mcp
sudo -u musicbrainz python -m venv venv
sudo -u musicbrainz venv/bin/pip install -e .

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable musicbrainz-mcp
sudo systemctl start musicbrainz-mcp

# Check status
sudo systemctl status musicbrainz-mcp
```

## Reverse Proxy Setup

### 1. Nginx Configuration

Create `/etc/nginx/sites-available/musicbrainz-mcp`:
```nginx
server {
    listen 80;
    server_name musicbrainz-mcp.example.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/musicbrainz-mcp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 2. Apache Configuration

Create `/etc/apache2/sites-available/musicbrainz-mcp.conf`:
```apache
<VirtualHost *:80>
    ServerName musicbrainz-mcp.example.com
    
    ProxyPreserveHost On
    ProxyPass / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/
    
    # WebSocket support
    RewriteEngine on
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://127.0.0.1:8000/$1" [P,L]
</VirtualHost>
```

Enable:
```bash
sudo a2enmod proxy proxy_http proxy_wstunnel rewrite
sudo a2ensite musicbrainz-mcp
sudo systemctl reload apache2
```

## SSL/TLS Configuration

### 1. Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d musicbrainz-mcp.example.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Self-Signed Certificate

```bash
# Generate certificate
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/musicbrainz-mcp.key \
  -out /etc/ssl/certs/musicbrainz-mcp.crt

# Update nginx config
server {
    listen 443 ssl;
    ssl_certificate /etc/ssl/certs/musicbrainz-mcp.crt;
    ssl_certificate_key /etc/ssl/private/musicbrainz-mcp.key;
    # ... rest of config
}
```

## Monitoring and Logging

### 1. Health Checks

The server provides a health endpoint at `/health`:
```bash
curl http://localhost:8000/health
```

### 2. Log Configuration

Configure structured logging:
```json
{
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "/var/log/musicbrainz-mcp/app.log"
  }
}
```

### 3. Prometheus Metrics

Add metrics endpoint:
```python
# In main.py
from prometheus_client import make_asgi_app

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
```

## Security Considerations

### 1. Environment Security

- Use environment variables for sensitive config
- Restrict file permissions (600 for config files)
- Run as non-root user
- Use secrets management for production

### 2. Network Security

- Use HTTPS in production
- Implement rate limiting at proxy level
- Use firewall rules to restrict access
- Monitor for unusual traffic patterns

### 3. Container Security

```dockerfile
# Use non-root user
USER 1000:1000

# Read-only filesystem
--read-only --tmpfs /tmp

# Drop capabilities
--cap-drop=ALL
```

## Backup and Recovery

### 1. Configuration Backup

```bash
# Backup config
tar -czf musicbrainz-mcp-config-$(date +%Y%m%d).tar.gz \
  config.json \
  /etc/systemd/system/musicbrainz-mcp.service

# Restore config
tar -xzf musicbrainz-mcp-config-20231201.tar.gz
```

### 2. Application Backup

```bash
# Backup application
tar -czf musicbrainz-mcp-app-$(date +%Y%m%d).tar.gz \
  /opt/musicbrainz-mcp \
  --exclude=venv \
  --exclude=__pycache__
```

## Troubleshooting Deployment

### 1. Common Issues

**Port already in use:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Permission denied:**
```bash
sudo chown -R musicbrainz:musicbrainz /opt/musicbrainz-mcp
sudo chmod +x /opt/musicbrainz-mcp/venv/bin/python
```

**Service won't start:**
```bash
sudo journalctl -u musicbrainz-mcp -f
sudo systemctl status musicbrainz-mcp
```

### 2. Performance Tuning

**For high traffic:**
- Increase worker processes
- Enable caching with longer TTL
- Use connection pooling
- Implement request queuing

**For low latency:**
- Reduce cache TTL
- Increase rate limits (if allowed)
- Use faster storage for cache
- Optimize network configuration

This deployment guide covers most common scenarios. Choose the deployment method that best fits your infrastructure and requirements.
