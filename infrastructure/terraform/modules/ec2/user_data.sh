#!/bin/bash

# Log everything
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1
echo "$(date): User data script started"

# Update system first
echo "$(date): Updating system"
dnf update -y

# Install essential packages
echo "$(date): Installing essential packages"
dnf install -y bind-utils curl

# Install and configure SSM Agent (required for Amazon Linux 2023)
echo "$(date): Checking SSM Agent installation"
if ! systemctl list-unit-files amazon-ssm-agent.service >/dev/null 2>&1; then
    echo "$(date): SSM Agent not found, installing..."
    dnf install -y amazon-ssm-agent
else
    echo "$(date): SSM Agent already installed"
fi

# Configure and start SSM Agent
echo "$(date): Configuring SSM Agent"
systemctl enable amazon-ssm-agent
systemctl restart amazon-ssm-agent

# Install Docker
echo "$(date): Installing Docker"
dnf install -y docker
systemctl enable docker
systemctl start docker

# Install Docker Compose
echo "$(date): Installing Docker Compose"
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create meilisearch directory
echo "$(date): Setting up Meilisearch"
mkdir -p /opt/meilisearch
cd /opt/meilisearch

# Create docker-compose.yml for Meilisearch
cat << 'EOF' > docker-compose.yml
version: '3.8'

services:
  meilisearch:
    image: getmeili/meilisearch:v1.16
    container_name: meilisearch
    restart: unless-stopped
    ports:
      - "7700:7700"
    environment:
      - MEILI_MASTER_KEY=${meilisearch_master_key}
      - MEILI_ENV=production
      - MEILI_DB_PATH=/data.ms
      - MEILI_HTTP_ADDR=0.0.0.0:7700
      - MEILI_LOG_LEVEL=INFO
      - MEILI_MAX_INDEXING_MEMORY=512Mb
      - MEILI_MAX_INDEXING_THREADS=2
    volumes:
      - meilisearch_data:/data.ms
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:7700/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

volumes:
  meilisearch_data:
    driver: local
EOF

# Create systemd service for Meilisearch
cat << 'EOF' > /etc/systemd/system/meilisearch.service
[Unit]
Description=Meilisearch Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/meilisearch
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Create backup script
cat << 'EOF' > /opt/meilisearch/backup.sh
#!/bin/bash

BACKUP_DIR="/tmp/meilisearch-backup"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="meilisearch_backup_$TIMESTAMP.tar.gz"
S3_BUCKET="${backup_bucket}"
REGION="${region}"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create Meilisearch dump
curl -X POST "http://localhost:7700/dumps" \
  -H "Authorization: Bearer ${meilisearch_master_key}" \
  -H "Content-Type: application/json"

# Wait for dump to complete (check status)
sleep 30

# Get the latest dump file from container
DUMP_FILE=$(docker exec meilisearch ls -t /data.ms/dumps/ | head -n 1)
if [ ! -z "$DUMP_FILE" ]; then
    docker cp meilisearch:/data.ms/dumps/$DUMP_FILE $BACKUP_DIR/
    
    # Create compressed archive
    cd $BACKUP_DIR
    tar -czf $BACKUP_FILE $DUMP_FILE
    
    # Upload to S3
    aws s3 cp $BACKUP_FILE s3://$S3_BUCKET/ --region $REGION
    
    # Cleanup
    rm -rf $BACKUP_DIR
    
    echo "Backup completed: $BACKUP_FILE uploaded to s3://$S3_BUCKET/"
else
    echo "Failed to create backup - no dump file found"
    exit 1
fi
EOF

# Make backup script executable
chmod +x /opt/meilisearch/backup.sh

# Create cron job for daily backups at 2 AM
cat << 'EOF' > /etc/cron.d/meilisearch-backup
0 2 * * * root /opt/meilisearch/backup.sh >> /var/log/meilisearch-backup.log 2>&1
EOF

# Create log rotation for backup logs
cat << 'EOF' > /etc/logrotate.d/meilisearch-backup
/var/log/meilisearch-backup.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 644 root root
}
EOF

# Create health check script
cat << 'EOF' > /opt/meilisearch/health-check.sh
#!/bin/bash

HEALTH_URL="http://localhost:7700/health"
MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -f -s $HEALTH_URL > /dev/null; then
        echo "Meilisearch is healthy"
        exit 0
    else
        echo "Health check failed, attempt $((RETRY_COUNT + 1))/$MAX_RETRIES"
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 5
    fi
done

echo "Meilisearch health check failed after $MAX_RETRIES attempts"
# Restart the service
systemctl restart meilisearch
exit 1
EOF

chmod +x /opt/meilisearch/health-check.sh

# Create health check cron job (every 5 minutes)
cat << 'EOF' > /etc/cron.d/meilisearch-health
*/5 * * * * root /opt/meilisearch/health-check.sh >> /var/log/meilisearch-health.log 2>&1
EOF

# Enable and start services
systemctl daemon-reload
systemctl enable meilisearch
systemctl start meilisearch

# Wait for Meilisearch to start
sleep 60

# Create receipts index with initial configuration
curl -X POST "http://localhost:7700/indexes" \
  -H "Authorization: Bearer ${meilisearch_master_key}" \
  -H "Content-Type: application/json" \
  -d '{
    "uid": "receipts",
    "primaryKey": "receipt_id"
  }'

# Configure searchable attributes
curl -X PUT "http://localhost:7700/indexes/receipts/settings/searchable-attributes" \
  -H "Authorization: Bearer ${meilisearch_master_key}" \
  -H "Content-Type: application/json" \
  -d '[
    "extracted_text",
    "file_name",
    "structured_data"
  ]'

# Configure filterable attributes
curl -X PUT "http://localhost:7700/indexes/receipts/settings/filterable-attributes" \
  -H "Authorization: Bearer ${meilisearch_master_key}" \
  -H "Content-Type: application/json" \
  -d '[
    "user_id",
    "upload_date",
    "processing_status",
    "extracted_date"
  ]'

# Configure sortable attributes
curl -X PUT "http://localhost:7700/indexes/receipts/settings/sortable-attributes" \
  -H "Authorization: Bearer ${meilisearch_master_key}" \
  -H "Content-Type: application/json" \
  -d '[
    "upload_date",
    "extracted_date",
    "file_name"
  ]'

# Configure typo tolerance
curl -X PUT "http://localhost:7700/indexes/receipts/settings/typo-tolerance" \
  -H "Authorization: Bearer ${meilisearch_master_key}" \
  -H "Content-Type: application/json" \
  -d '{
    "enabled": true,
    "minWordSizeForTypos": {
      "oneTypo": 5,
      "twoTypos": 9
    }
  }'

# Log completion
echo "$(date): Meilisearch setup completed" >> /var/log/meilisearch-setup.log
echo "$(date): User data script completed successfully"
