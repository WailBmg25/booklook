# BookLook Google Cloud Platform Deployment Guide

This guide provides step-by-step instructions for deploying BookLook on Google Cloud Platform (GCP) using Compute Engine and optionally Cloud SQL.

## Table of Contents

- [GCP Setup](#gcp-setup)
- [Compute Engine Deployment](#compute-engine-deployment)
- [Cloud SQL Alternative](#cloud-sql-alternative)
- [Load Balancer Configuration](#load-balancer-configuration)
- [Cloud Storage Integration](#cloud-storage-integration)
- [Monitoring and Logging](#monitoring-and-logging)
- [Cost Optimization](#cost-optimization)
- [Scaling Strategy](#scaling-strategy)

## GCP Setup

### Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed locally
- Project created in GCP Console

### 1. Install and Configure gcloud CLI

```bash
# Install gcloud CLI (macOS)
brew install --cask google-cloud-sdk

# Install gcloud CLI (Linux)
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize gcloud
gcloud init

# Login
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Set default region and zone
gcloud config set compute/region us-central1
gcloud config set compute/zone us-central1-a
```

### 2. Enable Required APIs

```bash
# Enable Compute Engine API
gcloud services enable compute.googleapis.com

# Enable Cloud SQL API (if using Cloud SQL)
gcloud services enable sqladmin.googleapis.com

# Enable Cloud Storage API
gcloud services enable storage-api.googleapis.com

# Enable Cloud Logging API
gcloud services enable logging.googleapis.com

# Enable Cloud Monitoring API
gcloud services enable monitoring.googleapis.com
```

### 3. Set Up VPC Network

```bash
# Create VPC network
gcloud compute networks create booklook-network \
    --subnet-mode=custom \
    --bgp-routing-mode=regional

# Create subnet
gcloud compute networks subnets create booklook-subnet \
    --network=booklook-network \
    --region=us-central1 \
    --range=10.0.0.0/24

# Create firewall rules
# Allow SSH
gcloud compute firewall-rules create booklook-allow-ssh \
    --network=booklook-network \
    --allow=tcp:22 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow SSH access"

# Allow HTTP/HTTPS
gcloud compute firewall-rules create booklook-allow-http \
    --network=booklook-network \
    --allow=tcp:80,tcp:443 \
    --source-ranges=0.0.0.0/0 \
    --description="Allow HTTP and HTTPS"

# Allow internal communication
gcloud compute firewall-rules create booklook-allow-internal \
    --network=booklook-network \
    --allow=tcp:0-65535,udp:0-65535,icmp \
    --source-ranges=10.0.0.0/24 \
    --description="Allow internal communication"
```

## Compute Engine Deployment

### Instance Specifications

#### Small Dataset (< 50GB)

```bash
MACHINE_TYPE="n2-standard-4"      # 4 vCPUs, 16 GB RAM
BOOT_DISK_SIZE="200GB"
BOOT_DISK_TYPE="pd-ssd"
```

#### Medium Dataset (50-200GB)

```bash
MACHINE_TYPE="n2-standard-8"      # 8 vCPUs, 32 GB RAM
BOOT_DISK_SIZE="500GB"
BOOT_DISK_TYPE="pd-ssd"
```

#### Large Dataset (200GB+)

```bash
MACHINE_TYPE="n2-standard-16"     # 16 vCPUs, 64 GB RAM
BOOT_DISK_SIZE="1000GB"
BOOT_DISK_TYPE="pd-ssd"
```

### 1. Create Compute Engine Instance

```bash
# Set variables
PROJECT_ID="your-project-id"
INSTANCE_NAME="booklook-prod"
MACHINE_TYPE="n2-standard-16"
ZONE="us-central1-a"
BOOT_DISK_SIZE="1000GB"
BOOT_DISK_TYPE="pd-ssd"

# Create instance
gcloud compute instances create $INSTANCE_NAME \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=$MACHINE_TYPE \
    --network-interface=network-tier=PREMIUM,subnet=booklook-subnet \
    --maintenance-policy=MIGRATE \
    --provisioning-model=STANDARD \
    --service-account=default \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --tags=http-server,https-server \
    --create-disk=auto-delete=yes,boot=yes,device-name=$INSTANCE_NAME,image=projects/ubuntu-os-cloud/global/images/ubuntu-2204-jammy-v20240319,mode=rw,size=$BOOT_DISK_SIZE,type=projects/$PROJECT_ID/zones/$ZONE/diskTypes/$BOOT_DISK_TYPE \
    --no-shielded-secure-boot \
    --shielded-vtpm \
    --shielded-integrity-monitoring \
    --labels=environment=production,app=booklook \
    --reservation-affinity=any

# Get instance IP
gcloud compute instances describe $INSTANCE_NAME \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

### 2. Create Persistent Disk for Data

```bash
# Create disk for database data
gcloud compute disks create booklook-data-disk \
    --size=500GB \
    --type=pd-ssd \
    --zone=$ZONE

# Attach disk to instance
gcloud compute instances attach-disk $INSTANCE_NAME \
    --disk=booklook-data-disk \
    --zone=$ZONE

# SSH into instance
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE

# Format and mount disk
sudo mkfs.ext4 -m 0 -E lazy_itable_init=0,lazy_journal_init=0,discard /dev/sdb
sudo mkdir -p /mnt/data
sudo mount -o discard,defaults /dev/sdb /mnt/data
sudo chmod a+w /mnt/data

# Add to fstab for auto-mount
echo UUID=$(sudo blkid -s UUID -o value /dev/sdb) /mnt/data ext4 discard,defaults,nofail 0 2 | sudo tee -a /etc/fstab
```

### 3. Install Docker and Application

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker (follow dedicated server guide)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt-get install -y docker-compose-plugin

# Logout and login again
exit
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE

# Clone repository
git clone <your-repository-url> /home/$USER/booklook
cd /home/$USER/booklook

# Configure environment
cp .env.production.example .env.production
nano .env.production

# Update docker-compose to use persistent disk
mkdir -p /mnt/data/postgres
mkdir -p /mnt/data/redis
mkdir -p /mnt/data/backups

# Deploy application
./deploy.sh deploy
```

### 4. Configure Startup Script

```bash
# Create startup script
sudo nano /usr/local/bin/booklook-startup.sh
```

Add:

```bash
#!/bin/bash
cd /home/$USER/booklook
docker-compose -f docker-compose.prod.yml up -d
```

```bash
# Make executable
sudo chmod +x /usr/local/bin/booklook-startup.sh

# Create systemd service
sudo nano /etc/systemd/system/booklook.service
```

Add:

```ini
[Unit]
Description=BookLook Application
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/$USER/booklook
ExecStart=/usr/local/bin/booklook-startup.sh
ExecStop=/usr/bin/docker-compose -f docker-compose.prod.yml down
User=$USER

[Install]
WantedBy=multi-user.target
```

```bash
# Enable service
sudo systemctl daemon-reload
sudo systemctl enable booklook
sudo systemctl start booklook
```

## Cloud SQL Alternative

For managed PostgreSQL, use Cloud SQL instead of self-hosted:

### 1. Create Cloud SQL Instance

```bash
# Set variables
INSTANCE_NAME="booklook-db"
DATABASE_VERSION="POSTGRES_15"
TIER="db-custom-16-65536"  # 16 vCPUs, 64 GB RAM
REGION="us-central1"
STORAGE_SIZE="500GB"
STORAGE_TYPE="PD_SSD"

# Create instance
gcloud sql instances create $INSTANCE_NAME \
    --database-version=$DATABASE_VERSION \
    --tier=$TIER \
    --region=$REGION \
    --storage-size=$STORAGE_SIZE \
    --storage-type=$STORAGE_TYPE \
    --storage-auto-increase \
    --backup \
    --backup-start-time=02:00 \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=03 \
    --database-flags=max_connections=200,shared_buffers=16GB,effective_cache_size=48GB

# Create database
gcloud sql databases create booklook_production \
    --instance=$INSTANCE_NAME

# Create user
gcloud sql users create booklook_user \
    --instance=$INSTANCE_NAME \
    --password=<strong-password>

# Get connection name
gcloud sql instances describe $INSTANCE_NAME \
    --format='get(connectionName)'
```

### 2. Configure Cloud SQL Proxy

```bash
# On Compute Engine instance
# Download Cloud SQL Proxy
wget https://dl.google.com/cloudsql/cloud_sql_proxy.linux.amd64 -O cloud_sql_proxy
chmod +x cloud_sql_proxy

# Create systemd service
sudo nano /etc/systemd/system/cloud-sql-proxy.service
```

Add:

```ini
[Unit]
Description=Cloud SQL Proxy
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=/home/$USER/cloud_sql_proxy -instances=PROJECT:REGION:INSTANCE=tcp:5432
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable cloud-sql-proxy
sudo systemctl start cloud-sql-proxy

# Update .env.production
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### 3. Cloud SQL Cost Optimization

```bash
# Enable automatic storage increase
gcloud sql instances patch $INSTANCE_NAME \
    --storage-auto-increase

# Configure maintenance window
gcloud sql instances patch $INSTANCE_NAME \
    --maintenance-window-day=SUN \
    --maintenance-window-hour=03

# Enable high availability (optional, increases cost)
gcloud sql instances patch $INSTANCE_NAME \
    --availability-type=REGIONAL
```

## Load Balancer Configuration

### 1. Create Instance Group

```bash
# Create instance template
gcloud compute instance-templates create booklook-template \
    --machine-type=n2-standard-8 \
    --network-interface=network=booklook-network,subnet=booklook-subnet \
    --tags=http-server,https-server \
    --image-family=ubuntu-2204-lts \
    --image-project=ubuntu-os-cloud \
    --boot-disk-size=200GB \
    --boot-disk-type=pd-ssd \
    --metadata-from-file=startup-script=startup.sh

# Create managed instance group
gcloud compute instance-groups managed create booklook-group \
    --base-instance-name=booklook \
    --template=booklook-template \
    --size=2 \
    --zone=us-central1-a

# Configure autoscaling
gcloud compute instance-groups managed set-autoscaling booklook-group \
    --max-num-replicas=10 \
    --min-num-replicas=2 \
    --target-cpu-utilization=0.75 \
    --cool-down-period=90 \
    --zone=us-central1-a
```

### 2. Create Load Balancer

```bash
# Create health check
gcloud compute health-checks create http booklook-health-check \
    --port=80 \
    --request-path=/health \
    --check-interval=10s \
    --timeout=5s \
    --unhealthy-threshold=3 \
    --healthy-threshold=2

# Create backend service
gcloud compute backend-services create booklook-backend \
    --protocol=HTTP \
    --health-checks=booklook-health-check \
    --global

# Add instance group to backend
gcloud compute backend-services add-backend booklook-backend \
    --instance-group=booklook-group \
    --instance-group-zone=us-central1-a \
    --global

# Create URL map
gcloud compute url-maps create booklook-lb \
    --default-service=booklook-backend

# Create target HTTP proxy
gcloud compute target-http-proxies create booklook-http-proxy \
    --url-map=booklook-lb

# Create forwarding rule
gcloud compute forwarding-rules create booklook-http-rule \
    --global \
    --target-http-proxy=booklook-http-proxy \
    --ports=80

# Get load balancer IP
gcloud compute forwarding-rules describe booklook-http-rule \
    --global \
    --format='get(IPAddress)'
```

### 3. Configure SSL

```bash
# Create SSL certificate
gcloud compute ssl-certificates create booklook-cert \
    --domains=yourdomain.com,www.yourdomain.com

# Create target HTTPS proxy
gcloud compute target-https-proxies create booklook-https-proxy \
    --url-map=booklook-lb \
    --ssl-certificates=booklook-cert

# Create HTTPS forwarding rule
gcloud compute forwarding-rules create booklook-https-rule \
    --global \
    --target-https-proxy=booklook-https-proxy \
    --ports=443
```

## Cloud Storage Integration

### 1. Create Storage Bucket

```bash
# Create bucket for backups
gsutil mb -c STANDARD -l us-central1 gs://booklook-backups-$PROJECT_ID

# Set lifecycle policy
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://booklook-backups-$PROJECT_ID

# Enable versioning
gsutil versioning set on gs://booklook-backups-$PROJECT_ID
```

### 2. Configure Automated Backups

```bash
# Create backup script
cat > /home/$USER/backup-to-gcs.sh << 'EOF'
#!/bin/bash
cd /home/$USER/booklook
./backup.sh full
gsutil -m cp backups/*.gz gs://booklook-backups-$PROJECT_ID/$(date +%Y/%m/%d)/
EOF

chmod +x /home/$USER/backup-to-gcs.sh

# Add to crontab
crontab -e
```

Add:

```cron
0 2 * * * /home/$USER/backup-to-gcs.sh
```

## Monitoring and Logging

### 1. Cloud Monitoring

```bash
# Install monitoring agent
curl -sSO https://dl.google.com/cloudagents/add-google-cloud-ops-agent-repo.sh
sudo bash add-google-cloud-ops-agent-repo.sh --also-install

# Configure monitoring
sudo nano /etc/google-cloud-ops-agent/config.yaml
```

Add:

```yaml
logging:
  receivers:
    syslog:
      type: files
      include_paths:
        - /var/log/syslog
    booklook:
      type: files
      include_paths:
        - /home/$USER/booklook/logs/*.log
  service:
    pipelines:
      default_pipeline:
        receivers: [syslog, booklook]

metrics:
  receivers:
    hostmetrics:
      type: hostmetrics
      collection_interval: 60s
  service:
    pipelines:
      default_pipeline:
        receivers: [hostmetrics]
```

```bash
# Restart agent
sudo systemctl restart google-cloud-ops-agent
```

### 2. Create Alerts

```bash
# Create alert policy for high CPU
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="High CPU Usage" \
    --condition-display-name="CPU > 80%" \
    --condition-threshold-value=0.8 \
    --condition-threshold-duration=300s \
    --condition-filter='resource.type="gce_instance" AND metric.type="compute.googleapis.com/instance/cpu/utilization"'

# Create alert for disk space
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Low Disk Space" \
    --condition-display-name="Disk > 85%" \
    --condition-threshold-value=0.85 \
    --condition-threshold-duration=300s \
    --condition-filter='resource.type="gce_instance" AND metric.type="compute.googleapis.com/instance/disk/utilization"'
```

### 3. Log Analysis

```bash
# View logs in Cloud Console
gcloud logging read "resource.type=gce_instance" --limit=50

# Create log-based metric
gcloud logging metrics create error_count \
    --description="Count of error logs" \
    --log-filter='severity>=ERROR'
```

## Cost Optimization

### 1. Committed Use Discounts

```bash
# Purchase 1-year commitment for 16 vCPU, 64 GB RAM
gcloud compute commitments create booklook-commitment \
    --region=us-central1 \
    --resources=vcpu=16,memory=64GB \
    --plan=12-month
```

### 2. Preemptible Instances (Development/Staging)

```bash
# Create preemptible instance (up to 80% discount)
gcloud compute instances create booklook-dev \
    --machine-type=n2-standard-8 \
    --preemptible \
    --zone=us-central1-a
```

### 3. Cost Monitoring

```bash
# Set budget alert
gcloud billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="BookLook Monthly Budget" \
    --budget-amount=1000USD \
    --threshold-rule=percent=50 \
    --threshold-rule=percent=90 \
    --threshold-rule=percent=100
```

### Monthly Cost Estimates

#### Small Deployment (n2-standard-4, 200GB SSD)
- Compute Engine: ~$150/month
- Storage: ~$40/month
- Network: ~$20/month
- **Total**: ~$210/month

#### Medium Deployment (n2-standard-8, 500GB SSD)
- Compute Engine: ~$300/month
- Storage: ~$100/month
- Network: ~$50/month
- **Total**: ~$450/month

#### Large Deployment (n2-standard-16, 1TB SSD)
- Compute Engine: ~$600/month
- Storage: ~$200/month
- Network: ~$100/month
- Cloud SQL (optional): ~$500/month
- **Total**: ~$900-1400/month

*Prices are estimates and vary by region. Use committed use discounts for 30-50% savings.*

## Scaling Strategy

### Vertical Scaling

```bash
# Stop instance
gcloud compute instances stop $INSTANCE_NAME --zone=$ZONE

# Change machine type
gcloud compute instances set-machine-type $INSTANCE_NAME \
    --machine-type=n2-standard-32 \
    --zone=$ZONE

# Start instance
gcloud compute instances start $INSTANCE_NAME --zone=$ZONE
```

### Horizontal Scaling

```bash
# Increase instance group size
gcloud compute instance-groups managed resize booklook-group \
    --size=5 \
    --zone=us-central1-a

# Update autoscaling
gcloud compute instance-groups managed set-autoscaling booklook-group \
    --max-num-replicas=20 \
    --min-num-replicas=5 \
    --zone=us-central1-a
```

## Disaster Recovery

### 1. Automated Snapshots

```bash
# Create snapshot schedule
gcloud compute resource-policies create snapshot-schedule booklook-daily \
    --region=us-central1 \
    --max-retention-days=14 \
    --on-source-disk-delete=keep-auto-snapshots \
    --daily-schedule \
    --start-time=02:00

# Attach to disk
gcloud compute disks add-resource-policies booklook-data-disk \
    --resource-policies=booklook-daily \
    --zone=us-central1-a
```

### 2. Cross-Region Backup

```bash
# Create bucket in different region
gsutil mb -c STANDARD -l us-east1 gs://booklook-backups-dr-$PROJECT_ID

# Sync backups
gsutil -m rsync -r gs://booklook-backups-$PROJECT_ID gs://booklook-backups-dr-$PROJECT_ID
```

## Troubleshooting

### Check Instance Status

```bash
gcloud compute instances describe $INSTANCE_NAME --zone=$ZONE
```

### View Serial Console

```bash
gcloud compute instances get-serial-port-output $INSTANCE_NAME --zone=$ZONE
```

### SSH Issues

```bash
# Reset SSH keys
gcloud compute config-ssh

# Use IAP tunnel
gcloud compute ssh $INSTANCE_NAME --zone=$ZONE --tunnel-through-iap
```

## Security Best Practices

1. **Use service accounts** with minimal permissions
2. **Enable VPC Service Controls** for data protection
3. **Use Cloud Armor** for DDoS protection
4. **Enable audit logging** for compliance
5. **Use Secret Manager** for sensitive data
6. **Regular security scanning** with Cloud Security Scanner
7. **Implement IAM policies** with least privilege

## Next Steps

1. Set up monitoring dashboards
2. Configure alerting policies
3. Test disaster recovery procedures
4. Optimize costs with committed use
5. Implement CI/CD pipeline
6. Set up staging environment

## Support Resources

- [GCP Documentation](https://cloud.google.com/docs)
- [Compute Engine Pricing](https://cloud.google.com/compute/pricing)
- [Cloud SQL Pricing](https://cloud.google.com/sql/pricing)
- [GCP Support](https://cloud.google.com/support)

---

**Last Updated**: 2024
**Version**: 1.0
