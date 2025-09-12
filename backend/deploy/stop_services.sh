#!/bin/bash

# AWS Infrastructure Stop Script (Non-destructive)
# This script stops services to save costs while preserving data and configuration

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[STOP]${NC} $1"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../../infrastructure/terraform"

print_header "AWS Receipt Search Infrastructure - STOP Services"
echo "=================================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "$TERRAFORM_DIR/main.tf" ]]; then
    print_error "Terraform directory not found at: $TERRAFORM_DIR"
    exit 1
fi

# Get AWS region and configuration
AWS_REGION=${AWS_REGION:-ap-southeast-1}
cd "$TERRAFORM_DIR"

print_status "🛑 STOPPING SERVICES (Data will be preserved)"
print_status "This will stop AWS services to save costs while keeping all data safe."
echo ""

print_warning "Services that will be STOPPED:"
print_warning "✋ EC2 Instance (Meilisearch) - ~$20/month savings"
print_warning "✋ Lambda concurrency limits - Minimal cost"
echo ""

print_warning "Services that will REMAIN ACTIVE (low/no cost):"
print_warning "✅ S3 buckets and data - ~$1-5/month"
print_warning "✅ DynamoDB tables and data - ~$0-5/month" 
print_warning "✅ VPC and networking - ~$32/month (NAT Gateway)"
print_warning "✅ API Gateway - Pay per request"
print_warning "✅ Cognito - Pay per user"
echo ""

read -p "Continue with stopping services? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_status "Operation cancelled."
    exit 0
fi

echo ""
print_header "Step 1: Stopping EC2 Instance (Meilisearch)"

# Get EC2 instance ID
INSTANCE_ID=$(terraform output -raw meilisearch_instance_id 2>/dev/null || echo "")

if [[ -n "$INSTANCE_ID" ]]; then
    # Check current state
    INSTANCE_STATE=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null || echo "not-found")
    
    print_status "Current instance state: $INSTANCE_STATE"
    
    if [[ "$INSTANCE_STATE" == "running" ]]; then
        print_status "Stopping EC2 instance: $INSTANCE_ID"
        aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
        
        print_status "Waiting for instance to stop..."
        aws ec2 wait instance-stopped --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
        print_status "✅ EC2 instance stopped successfully"
        
        # Calculate savings
        print_status "💰 Estimated savings: ~$20/month while stopped"
    elif [[ "$INSTANCE_STATE" == "stopped" ]]; then
        print_status "✅ EC2 instance already stopped"
    else
        print_warning "⚠️  Instance in state: $INSTANCE_STATE (may be stopping/starting)"
    fi
else
    print_error "❌ Could not find EC2 instance ID from Terraform outputs"
fi

echo ""
print_header "Step 2: Setting Lambda Concurrency Limits (Optional Cost Control)"

print_status "Setting Lambda reserved concurrency to limit costs..."

LAMBDA_FUNCTIONS=(
    "receipt-search-dev-api"
    "receipt-search-dev-image-processor"
    "receipt-search-dev-text-extractor"
    "receipt-search-dev-cleanup-worker"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if aws lambda get-function --function-name "$func" --region "$AWS_REGION" >/dev/null 2>&1; then
        print_status "Setting concurrency limit for: $func"
        # Set low concurrency to prevent unexpected high costs
        aws lambda put-reserved-concurrency-configuration \
            --function-name "$func" \
            --reserved-concurrent-executions 5 \
            --region "$AWS_REGION" 2>/dev/null || true
    fi
done

echo ""
print_header "Step 3: Status Summary"

# Show current costs and status
print_status "📊 Current Service Status After Stop:"
echo ""

# EC2 Status
if [[ -n "$INSTANCE_ID" ]]; then
    CURRENT_STATE=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null || echo "unknown")
    if [[ "$CURRENT_STATE" == "stopped" ]]; then
        print_status "🛑 EC2 (Meilisearch): STOPPED - Saving ~$20/month"
    else
        print_warning "⚠️  EC2 (Meilisearch): $CURRENT_STATE"
    fi
fi

# Other services status
print_status "✅ S3 Buckets: ACTIVE (data preserved) - ~$1-5/month"
print_status "✅ DynamoDB: ACTIVE (data preserved) - ~$0-5/month"
print_status "✅ Lambda: ACTIVE (concurrency limited) - Minimal cost"
print_status "✅ API Gateway: ACTIVE - Pay per request"
print_status "✅ VPC/NAT Gateway: ACTIVE - ~$32/month"

echo ""
print_header "💰 Cost Impact Summary"
echo "======================="
print_status "Before stopping: ~$50-65/month"
print_status "After stopping:  ~$35-45/month"
print_status "Monthly savings: ~$15-20/month (30-40% reduction)"
echo ""

print_status "🔄 To restart services later, run: ./start_services.sh"
print_status "🗑️  To completely delete everything, run: ./cleanup.sh"

# Save stop timestamp for restart script
echo "STOPPED_AT=$(date '+%Y-%m-%d %H:%M:%S')" > /tmp/services_stopped.info
echo "INSTANCE_ID=$INSTANCE_ID" >> /tmp/services_stopped.info

cd - > /dev/null

echo ""
print_status "🎉 Services stopped successfully!"
print_status "Your data and configuration are preserved and ready to restart anytime."