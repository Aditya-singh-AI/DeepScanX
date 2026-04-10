# 🚀 Deployment Guide for DeepScanX AI

This guide covers deploying DeepScanX AI to production environments.

## 📋 Table of Contents

- [Pre-Deployment Checklist](#-pre-deployment-checklist)
- [Environment Setup](#-environment-setup)
- [Backend Deployment](#-backend-deployment)
- [Frontend Deployment](#-frontend-deployment)
- [Database Setup](#-database-setup)
- [Security Configuration](#-security-configuration)
- [Monitoring & Logging](#-monitoring--logging)
- [Troubleshooting](#-troubleshooting)

---

## ✅ Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] Environment variables configured
- [ ] Database backups created
- [ ] SSL certificates obtained
- [ ] Rate limiting configured
- [ ] CORS policies set
- [ ] Logging setup complete
- [ ] Monitoring alerts configured
- [ ] Security scan completed
- [ ] API keys secured

---

## 🔧 Environment Setup

### Production Environment Variables

Create a `.env.production` file:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=your-secret-key-min-32-chars
DEBUG=False

# Database
MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net/deepscanx?retryWrites=true&w=majority
DB_NAME=deepscanx_production

# Security
JWT_SECRET=your-jwt-secret-key
JWT_EXPIRATION=3600

# API Keys
GOOGLE_API_KEY=your-google-api-key
HUGGINGFACE_TOKEN=your-hf-token

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=5000
WORKERS=4

# CORS
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/deepscanx/app.log

# Email (for reports)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

---

## 🏗️ Backend Deployment

### Option 1: AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize EB application
eb init -p python-3.10 deepscanx-ai

# Create environment
eb create deepscanx-production

# Deploy
eb deploy

# Monitor
eb logs
eb open
```

### Option 2: Heroku

```bash
# Install Heroku CLI
brew tap heroku/brew && brew install heroku

# Login
heroku login

# Create app
heroku create deepscanx-ai

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

### Option 3: Docker (Any Cloud)

**Create Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/ .

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "run:app"]
```

**Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  web:
    build: ./backend
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - MONGO_URI=${MONGO_URI}
    depends_on:
      - mongodb
  
  mongodb:
    image: mongo:latest
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    environment:
      - MONGO_INITDB_DATABASE=deepscanx

volumes:
  mongodb_data:
```

**Deploy:**
```bash
docker-compose up -d
```

---

## 🎨 Frontend Deployment

### Option 1: Vercel (Recommended for React/Vite)

```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
cd frontend
vercel

# Production deployment
vercel --prod
```

### Option 2: Netlify

```bash
# Build
npm run build

# Install Netlify CLI
npm install -g netlify-cli

# Deploy
netlify deploy --prod --dir=dist
```

### Option 3: AWS S3 + CloudFront

```bash
# Build
npm run build

# Create S3 bucket
aws s3 mb s3://deepscanx-frontend

# Upload
aws s3 sync dist/ s3://deepscanx-frontend/

# Create CloudFront distribution
aws cloudfront create-distribution --distribution-config file://distribution-config.json
```

---

## 🗄️ Database Setup

### MongoDB Atlas (Recommended)

1. **Create Cluster:**
   - Go to MongoDB Atlas (https://www.mongodb.com/cloud/atlas)
   - Create free tier cluster
   - Configure backup settings

2. **Create Database User:**
   ```bash
   Username: deepscanx_prod_user
   Password: [strong-password]
   ```

3. **Add IP Whitelist:**
   - Add deployment server IP addresses
   - Or allow all (0.0.0.0/0) for cloud deployments

4. **Get Connection String:**
   ```
   mongodb+srv://deepscanx_prod_user:[password]@cluster0.xxxxx.mongodb.net/deepscanx?retryWrites=true&w=majority
   ```

### MongoDB Local/Self-Hosted

```bash
# Install MongoDB
# See: https://docs.mongodb.com/manual/installation/

# Start service
sudo systemctl start mongod

# Create backup
mongodump --out /path/to/backup

# Restore backup
mongorestore --dir /path/to/backup
```

---

## 🔒 Security Configuration

### SSL/TLS Certificates

**Using Let's Encrypt:**
```bash
# Install Certbot
sudo apt-get install certbot

# Obtain certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Auto-renew
sudo systemctl enable certbot.timer
```

### Nginx Configuration

```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Backend API
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_buffering off;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### CORS Configuration

```python
# In Flask app
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
```

---

## 📊 Monitoring & Logging

### Application Logging

```python
# backend/config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(app):
    if not app.debug:
        file_handler = RotatingFileHandler(
            '/var/log/deepscanx/app.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
```

### Error Tracking (Sentry)

```bash
# Install Sentry SDK
pip install sentry-sdk

# Configure
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[FlaskIntegration()],
    traces_sample_rate=0.1
)
```

### Monitoring Uptime

```bash
# Using Uptime Robot (https://uptimerobot.com)
# Add endpoints to monitor:
# - https://yourdomain.com/api/health
# - https://yourdomain.com/
```

---

## 🛠️ Troubleshooting

### Common Issues

**Issue: Database Connection Timeout**
```bash
# Check MongoDB service
sudo systemctl status mongod

# Check firewall
sudo ufw allow 27017

# Test connection
mongo "mongodb+srv://user:pass@cluster.mongodb.net/deepscanx"
```

**Issue: Out of Memory (ML Models)**
```bash
# Increase swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**Issue: High Latency**
```bash
# Check server load
top

# Check network
iftop

# Scale up resources or implement caching
```

---

## 📈 Performance Optimization

### Backend Caching
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@app.route('/api/models')
@cache.cached(timeout=3600)
def get_models():
    return Model.get_all()
```

### Image Optimization
```python
from PIL import Image

def optimize_image(image_path):
    img = Image.open(image_path)
    img.thumbnail((1024, 1024))
    img.save(image_path, quality=85, optimize=True)
```

---

## 📝 Post-Deployment

1. **Verify Deployment:**
   - Check all endpoints are working
   - Test file uploads
   - Verify database connectivity
   - Check SSL certificates

2. **Setup Backups:**
   - MongoDB automatic backups
   - Database snapshots
   - Regular testing of restore procedures

3. **Documentation:**
   - Document deployment procedures
   - Keep runbooks updated
   - Document any custom configurations

---

## 🆘 Support

- Issues: https://github.com/Aditya-singh-ai/DeepScanX-AI/issues
- Discussions: https://github.com/Aditya-singh-ai/DeepScanX-AI/discussions
- Email: deepscanx@example.com
