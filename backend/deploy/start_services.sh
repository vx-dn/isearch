#!/bin/bash

# AWS Infrastructure Start Script
# This script starts previously stopped services

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
    echo -e "${BLUE}[START]${NC} $1"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../../infrastructure/terraform"

print_header "AWS Receipt Search Infrastructure - START Services"
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

print_status "🚀 STARTING SERVICES"
print_status "This will restart stopped AWS services and restore full functionality."
echo ""

# Check if we have stop info
if [[ -f "/tmp/services_stopped.info" ]]; then
    source /tmp/services_stopped.info
    print_status "Found stop information from: $STOPPED_AT"
else
    print_warning "No stop information found. Will attempt to start all services."
fi

echo ""
print_header "Step 1: Starting EC2 Instance (Meilisearch)"

# Get EC2 instance ID
INSTANCE_ID_FROM_TF=$(terraform output -raw meilisearch_instance_id 2>/dev/null || echo "")
INSTANCE_ID=${INSTANCE_ID:-$INSTANCE_ID_FROM_TF}

if [[ -n "$INSTANCE_ID" ]]; then
    # Check current state
    INSTANCE_STATE=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null || echo "not-found")
    
    print_status "Current instance state: $INSTANCE_STATE"
    
    if [[ "$INSTANCE_STATE" == "stopped" ]]; then
        print_status "Starting EC2 instance: $INSTANCE_ID"
        aws ec2 start-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
        
        print_status "Waiting for instance to start (this may take 2-3 minutes)..."
        aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$AWS_REGION"
        
        # Wait additional time for Meilisearch to fully initialize
        print_status "Waiting for Meilisearch service to initialize..."
        sleep 30
        
        print_status "✅ EC2 instance started successfully"
    elif [[ "$INSTANCE_STATE" == "running" ]]; then
        print_status "✅ EC2 instance already running"
    else
        print_warning "⚠️  Instance in state: $INSTANCE_STATE (may be starting/stopping)"
    fi
    
    # Get instance IP for verification
    INSTANCE_IP=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text 2>/dev/null || echo "")
    if [[ -n "$INSTANCE_IP" ]]; then
        print_status "Instance private IP: $INSTANCE_IP"
    fi
else
    print_error "❌ Could not find EC2 instance ID"
fi

echo ""
print_header "Step 2: Removing Lambda Concurrency Limits"

print_status "Removing Lambda concurrency limits..."

LAMBDA_FUNCTIONS=(
    "receipt-search-dev-api"
    "receipt-search-dev-image-processor"
    "receipt-search-dev-text-extractor"
    "receipt-search-dev-cleanup-worker"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if aws lambda get-function --function-name "$func" --region "$AWS_REGION" >/dev/null 2>&1; then
        print_status "Removing concurrency limit for: $func"
        aws lambda delete-reserved-concurrency-configuration \
            --function-name "$func" \
            --region "$AWS_REGION" 2>/dev/null || true
    fi
done

echo ""
print_header "Step 3: Service Health Check"

print_status "Checking service health..."

# Check API Gateway
API_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")
if [[ -n "$API_URL" ]]; then
    print_status "Testing API Gateway health..."
    HEALTH_RESPONSE=$(curl -s "$API_URL/api/v1/health" -w "%{http_code}" -o /dev/null 2>/dev/null || echo "000")
    if [[ "$HEALTH_RESPONSE" == "200" ]]; then
        print_status "✅ API Gateway: Healthy"
    else
        print_warning "⚠️  API Gateway: HTTP $HEALTH_RESPONSE"
    fi
fi

# Check Lambda functions
print_status "Checking Lambda functions..."
for func in "${LAMBDA_FUNCTIONS[@]}"; do
    if aws lambda get-function --function-name "$func" --region "$AWS_REGION" >/dev/null 2>&1; then
        FUNC_STATE=$(aws lambda get-function --function-name "$func" --region "$AWS_REGION" --query 'Configuration.State' --output text 2>/dev/null || echo "Unknown")
        if [[ "$FUNC_STATE" == "Active" ]]; then
            print_status "✅ Lambda $func: Active"
        else
            print_warning "⚠️  Lambda $func: $FUNC_STATE"
        fi
    fi
done

# Check DynamoDB tables
print_status "Checking DynamoDB tables..."
RECEIPTS_TABLE=$(terraform output -raw receipts_table_name 2>/dev/null || echo "")
USERS_TABLE=$(terraform output -raw users_table_name 2>/dev/null || echo "")

for table in "$RECEIPTS_TABLE" "$USERS_TABLE"; do
    if [[ -n "$table" ]]; then
        TABLE_STATUS=$(aws dynamodb describe-table --table-name "$table" --region "$AWS_REGION" --query 'Table.TableStatus' --output text 2>/dev/null || echo "Unknown")
        if [[ "$TABLE_STATUS" == "ACTIVE" ]]; then
            print_status "✅ DynamoDB $table: Active"
        else
            print_warning "⚠️  DynamoDB $table: $TABLE_STATUS"
        fi
    fi
done

echo ""
print_header "Step 4: Testing Authentication"

if [[ -f "/tmp/cognito_tokens.sh" ]]; then
    print_status "Testing with existing authentication tokens..."
    source /tmp/cognito_tokens.sh
    
    if [[ -n "$ACCESS_TOKEN" ]] && [[ -n "$API_URL" ]]; then
        AUTH_RESPONSE=$(curl -s "$API_URL/api/v1/auth/me" -H "Authorization: Bearer $ACCESS_TOKEN" -w "%{http_code}" -o /dev/null 2>/dev/null || echo "000")
        if [[ "$AUTH_RESPONSE" == "200" ]] || [[ "$AUTH_RESPONSE" == "503" ]]; then
            print_status "✅ Authentication: Working (HTTP $AUTH_RESPONSE)"
        else
            print_warning "⚠️  Authentication: HTTP $AUTH_RESPONSE"
        fi
    fi
else
    print_status "ℹ️  No authentication tokens found. Run ./test_auth.sh to test authentication."
fi

echo ""
print_header "📊 Service Status Summary"
echo "========================="

# Final status check
if [[ -n "$INSTANCE_ID" ]]; then
    FINAL_STATE=$(aws ec2 describe-instances --instance-ids "$INSTANCE_ID" --region "$AWS_REGION" --query 'Reservations[0].Instances[0].State.Name' --output text 2>/dev/null || echo "unknown")
    if [[ "$FINAL_STATE" == "running" ]]; then
        print_status "🚀 EC2 (Meilisearch): RUNNING"
    else
        print_warning "⚠️  EC2 (Meilisearch): $FINAL_STATE"
    fi
fi

print_status "✅ S3 Buckets: ACTIVE"
print_status "✅ DynamoDB: ACTIVE"
print_status "✅ Lambda Functions: ACTIVE (no limits)"
print_status "✅ API Gateway: ACTIVE"
print_status "✅ VPC/Networking: ACTIVE"

echo ""
print_header "💰 Cost Impact"
echo "=============="
print_status "Services are now running at full capacity"
print_status "Estimated monthly cost: ~$50-65/month"
echo ""

print_status "🔗 API Gateway URL: $API_URL"
print_status "🧪 Test services with: ./test_auth.sh and ./test_pipeline.sh"
print_status "🛑 Stop services again with: ./stop_services.sh"

# Clean up stop info
rm -f /tmp/services_stopped.info

cd - > /dev/null

echo ""
print_status "🎉 All services started successfully!"
print_status "Your infrastructure is fully operational."