# VeriFast Production Deployment Guide

This guide covers deploying VeriFast to a production environment with all services properly configured.

## System Requirements

### Server Specifications
- **OS**: Ubuntu 22.04 LTS (recommended) or similar Linux distribution
- **CPU**: 2+ cores (4+ recommended for high traffic)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Storage**: 20GB+ SSD storage
- **Network**: Stable internet connection for external API calls

### Required Services
- **Python 3.10+**
- **PostgreSQL 14+** (database)
- **Redis 6+** (task queue and caching)
- **Nginx** (reverse proxy and static file serving)
- **Supervisor** (process management)

## Pre-Deployment Setup

### 1. Server Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv python3-dev \
    postgresql postgresql-contrib redis-server nginx supervisor \
    git curl build-essential libpq-dev

# Install Node.js (for frontend assets if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE verifast_prod;
CREATE USER verifast_user WITH PASSWORD 'your_secure_password_here';
ALTER ROLE verifast_user SET client_encoding TO 'utf8';
ALTER ROLE verifast_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE verifast_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE verifast_prod TO verifast_user;
\q
```

### 3. Redis Configuration

```bash
# Configure Redis for production
sudo nano /etc/redis/redis.conf

# Key settings to modify:
# maxmemory 256mb
# maxmemory-policy allkeys-lru
# save 900 1
# save 300 10

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

## Application Deployment

### 1. Application Setup

```bash
# Create application directory
sudo mkdir -p /var/www/verifast
sudo chown $USER:$USER /var/www/verifast
cd /var/www/verifast

# Clone repository
git clone https://github.com/yourusername/verifast.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy models
python -m spacy download en_core_web_sm
python -m spacy download es_core_news_sm
```

### 2. Environment Configuration

Create production environment file:

```bash
nano .env
```

```env
# Django Settings
DEBUG=False
SECRET_KEY=your-very-secure-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgres://verifast_user:your_secure_password_here@localhost:5432/verifast_prod

# AI Services
GEMINI_API_KEY=your-gemini-api-key-here
ENABLE_AI_FEATURES=true

# NLP Services
ENABLE_NLP_FEATURES=true
SPACY_MODEL_EN=en_core_web_sm
SPACY_MODEL_ES=es_core_news_sm

# External APIs
ENABLE_WIKIPEDIA_VALIDATION=true
ENABLE_ARTICLE_SCRAPING=true
WIKIPEDIA_USER_AGENT=VeriFastApp/1.0

# Redis/Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Performance
MAX_ARTICLE_LENGTH=100000
PROCESSING_TIMEOUT=300
CONCURRENT_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_SERVICE_ERRORS=true
```

### 3. Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### 4. Test Application

```bash
# Test the application
python manage.py check --deploy

# Run dependency validation
python scripts/validate_dependencies.py

# Run performance tests
python scripts/performance_test.py
```

## Process Management with Supervisor

### 1. Gunicorn Configuration

Create Gunicorn configuration:

```bash
sudo nano /etc/supervisor/conf.d/verifast_gunicorn.conf
```

```ini
[program:verifast_gunicorn]
command=/var/www/verifast/venv/bin/gunicorn config.wsgi:application --workers 3 --bind 127.0.0.1:8000 --timeout 300 --max-requests 1000 --max-requests-jitter 100
directory=/var/www/verifast
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/verifast/gunicorn.log
environment=PATH="/var/www/verifast/venv/bin"
```

### 2. Celery Worker Configuration

```bash
sudo nano /etc/supervisor/conf.d/verifast_celery.conf
```

```ini
[program:verifast_celery]
command=/var/www/verifast/venv/bin/celery -A config.celery worker --loglevel=info --concurrency=4
directory=/var/www/verifast
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/verifast/celery.log
environment=PATH="/var/www/verifast/venv/bin"
```

### 3. Celery Beat Configuration (for scheduled tasks)

```bash
sudo nano /etc/supervisor/conf.d/verifast_celerybeat.conf
```

```ini
[program:verifast_celerybeat]
command=/var/www/verifast/venv/bin/celery -A config.celery beat --loglevel=info --schedule=/var/www/verifast/celerybeat-schedule
directory=/var/www/verifast
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/verifast/celerybeat.log
environment=PATH="/var/www/verifast/venv/bin"
```

### 4. Create Log Directory and Update Supervisor

```bash
# Create log directory
sudo mkdir -p /var/log/verifast
sudo chown www-data:www-data /var/log/verifast

# Set proper permissions
sudo chown -R www-data:www-data /var/www/verifast

# Update supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

## Nginx Configuration

### 1. Create Nginx Site Configuration

```bash
sudo nano /etc/nginx/sites-available/verifast
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss;

    # Static files
    location /static/ {
        alias /var/www/verifast/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /var/www/verifast/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    # Favicon
    location = /favicon.ico {
        access_log off;
        log_not_found off;
    }

    # Health check endpoint (no auth required)
    location /health/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        access_log off;
    }

    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Buffer settings
        proxy_buffering on;
        proxy_buffer_size 128k;
        proxy_buffers 4 256k;
        proxy_busy_buffers_size 256k;
    }

    # Rate limiting for API endpoints
    location /api/ {
        limit_req zone=api burst=10 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Rate limiting configuration
http {
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
}
```

### 2. Enable Site and Configure SSL

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/verifast /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Install Certbot for SSL
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Test SSL renewal
sudo certbot renew --dry-run
```

## Monitoring and Maintenance

### 1. Log Management

```bash
# Configure log rotation
sudo nano /etc/logrotate.d/verifast
```

```
/var/log/verifast/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        supervisorctl restart verifast_gunicorn verifast_celery
    endscript
}
```

### 2. Backup Script

```bash
sudo nano /usr/local/bin/backup_verifast.sh
```

```bash
#!/bin/bash
BACKUP_DIR=/var/backups/verifast
DATETIME=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -U verifast_user -h localhost verifast_prod > $BACKUP_DIR/verifast_db_$DATETIME.sql

# Compress backup
gzip $BACKUP_DIR/verifast_db_$DATETIME.sql

# Keep only last 7 backups
ls -tp $BACKUP_DIR/verifast_db_*.sql.gz | grep -v '/$' | tail -n +8 | xargs -I {} rm -- {}

# Application files backup (optional)
tar -czf $BACKUP_DIR/verifast_app_$DATETIME.tar.gz -C /var/www verifast --exclude=verifast/venv --exclude=verifast/.git
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/backup_verifast.sh

# Add to crontab
sudo crontab -e
# Add: 0 2 * * * /usr/local/bin/backup_verifast.sh
```

### 3. Health Monitoring

```bash
sudo nano /usr/local/bin/health_check.sh
```

```bash
#!/bin/bash
HEALTH_URL="https://yourdomain.com/health/"
ALERT_EMAIL="admin@yourdomain.com"

RESPONSE=$(curl -s $HEALTH_URL)
STATUS=$(echo $RESPONSE | jq -r '.status' 2>/dev/null)

if [ "$STATUS" != "healthy" ]; then
    echo "VeriFast health check failed. Status: $STATUS" | mail -s "VeriFast Health Alert" $ALERT_EMAIL
    echo "$(date): Health check failed - $STATUS" >> /var/log/verifast/health.log
fi
```

```bash
# Make executable and add to crontab
sudo chmod +x /usr/local/bin/health_check.sh
sudo crontab -e
# Add: */15 * * * * /usr/local/bin/health_check.sh
```

## Security Hardening

### 1. Firewall Configuration

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Fail2Ban Configuration

```bash
# Install and configure Fail2Ban
sudo apt install -y fail2ban

sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
action = iptables-multiport[name=ReqLimit, port="http,https", protocol=tcp]
logpath = /var/log/nginx/error.log
findtime = 600
bantime = 7200
maxretry = 10
```

### 3. System Updates

```bash
# Enable automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Performance Optimization

### 1. Database Optimization

```bash
# PostgreSQL configuration
sudo nano /etc/postgresql/14/main/postgresql.conf
```

Key settings to adjust:
```
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
```

### 2. Redis Optimization

```bash
# Redis configuration for production
sudo nano /etc/redis/redis.conf
```

Key settings:
```
maxmemory 512mb
maxmemory-policy allkeys-lru
tcp-keepalive 300
timeout 300
```

## Troubleshooting

### Common Issues

**Service Not Starting:**
```bash
# Check supervisor status
sudo supervisorctl status

# Check logs
sudo tail -f /var/log/verifast/gunicorn.log
sudo tail -f /var/log/verifast/celery.log
```

**Database Connection Issues:**
```bash
# Test database connection
sudo -u postgres psql -d verifast_prod -c "SELECT version();"

# Check PostgreSQL status
sudo systemctl status postgresql
```

**High Memory Usage:**
```bash
# Monitor processes
htop
sudo supervisorctl restart verifast_celery
```

**SSL Certificate Issues:**
```bash
# Renew certificates
sudo certbot renew
sudo systemctl reload nginx
```

## Deployment Checklist

- [ ] Server provisioned with required specifications
- [ ] All system packages installed and updated
- [ ] PostgreSQL database created and configured
- [ ] Redis server installed and configured
- [ ] Application code deployed and dependencies installed
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Supervisor processes configured and running
- [ ] Nginx configured with SSL
- [ ] Firewall configured
- [ ] Monitoring and backup scripts installed
- [ ] Health checks passing
- [ ] Performance tests passing
- [ ] Security hardening applied

## Post-Deployment

1. **Monitor logs** for the first 24 hours
2. **Test all functionality** including article processing
3. **Verify backup scripts** are working
4. **Set up monitoring alerts**
5. **Document any custom configurations**
6. **Plan regular maintenance schedule**

For additional support, refer to the main documentation or create an issue in the project repository.