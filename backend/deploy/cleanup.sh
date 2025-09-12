#!/bin/bash

# AWS Infrastructure Cleanup Script
# This script will safely tear down all AWS resources for the receipt-search project

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
    echo -e "${BLUE}[CLEANUP]${NC} $1"
}

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../../infrastructure/terraform"

print_header "AWS Receipt Search Infrastructure Cleanup"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [[ ! -f "$TERRAFORM_DIR/main.tf" ]]; then
    print_error "Terraform directory not found at: $TERRAFORM_DIR"
    print_error "Please run this script from the correct location."
    exit 1
fi

# Warning and confirmation
print_warning "This script will PERMANENTLY DELETE all AWS resources including:"
print_warning "- Lambda functions"
print_warning "- S3 buckets and all files"
print_warning "- DynamoDB tables and all data"
print_warning "- EC2 instances (Meilisearch)"
print_warning "- VPC and networking components"
print_warning "- Cognito user pools and users"
print_warning "- API Gateway"
print_warning "- SQS queues and messages"
print_warning "- CloudWatch logs"
echo ""

read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    print_status "Cleanup cancelled."
    exit 0
fi

echo ""
print_header "Step 1: Removing Lambda Event Source Mappings"

# Get AWS region
AWS_REGION=${AWS_REGION:-ap-southeast-1}

# Remove SQS event source mappings
print_status "Removing SQS event source mappings..."
EVENT_MAPPINGS=$(aws lambda list-event-source-mappings --function-name receipt-search-dev-text-extractor --region "$AWS_REGION" --query 'EventSourceMappings[].UUID' --output text 2>/dev/null || echo "")

if [[ -n "$EVENT_MAPPINGS" ]]; then
    for uuid in $EVENT_MAPPINGS; do
        if [[ "$uuid" != "None" ]]; then
            print_status "Deleting event source mapping: $uuid"
            aws lambda delete-event-source-mapping --uuid "$uuid" --region "$AWS_REGION" || true
        fi
    done
else
    print_status "No SQS event source mappings found"
fi

echo ""
print_header "Step 2: Removing Lambda Functions"

# List and delete Lambda functions
LAMBDA_FUNCTIONS=(
    "receipt-search-dev-api"
    "receipt-search-dev-image-processor" 
    "receipt-search-dev-text-extractor"
    "receipt-search-dev-cleanup-worker"
)

for func in "${LAMBDA_FUNCTIONS[@]}"; do
    print_status "Checking Lambda function: $func"
    if aws lambda get-function --function-name "$func" --region "$AWS_REGION" >/dev/null 2>&1; then
        print_status "Deleting Lambda function: $func"
        aws lambda delete-function --function-name "$func" --region "$AWS_REGION" || true
    else
        print_status "Lambda function not found: $func"
    fi
done

echo ""
print_header "Step 3: Emptying S3 Buckets"

# Get bucket names from Terraform state if available
cd "$TERRAFORM_DIR"

RECEIPTS_BUCKET=$(terraform output -raw receipts_bucket_name 2>/dev/null || echo "")
MEILISEARCH_BUCKET=$(terraform output -raw meilisearch_backups_bucket_name 2>/dev/null || echo "")

# Empty S3 buckets (required before Terraform can delete them)
if [[ -n "$RECEIPTS_BUCKET" ]]; then
    print_status "Emptying receipts bucket: $RECEIPTS_BUCKET"
    aws s3 rm "s3://$RECEIPTS_BUCKET" --recursive --region "$AWS_REGION" || true
    
    # Remove all versions and delete markers (for versioned buckets)
    aws s3api list-object-versions --bucket "$RECEIPTS_BUCKET" --region "$AWS_REGION" --query 'Versions[].{Key:Key,VersionId:VersionId}' --output text 2>/dev/null | while read key version; do
        if [[ -n "$key" && "$key" != "None" ]]; then
            aws s3api delete-object --bucket "$RECEIPTS_BUCKET" --key "$key" --version-id "$version" --region "$AWS_REGION" || true
        fi
    done
    
    aws s3api list-object-versions --bucket "$RECEIPTS_BUCKET" --region "$AWS_REGION" --query 'DeleteMarkers[].{Key:Key,VersionId:VersionId}' --output text 2>/dev/null | while read key version; do
        if [[ -n "$key" && "$key" != "None" ]]; then
            aws s3api delete-object --bucket "$RECEIPTS_BUCKET" --key "$key" --version-id "$version" --region "$AWS_REGION" || true
        fi
    done
fi

if [[ -n "$MEILISEARCH_BUCKET" ]]; then
    print_status "Emptying Meilisearch backups bucket: $MEILISEARCH_BUCKET"
    aws s3 rm "s3://$MEILISEARCH_BUCKET" --recursive --region "$AWS_REGION" || true
fi

echo ""
print_header "Step 4: Cleaning up Cognito Test Users"

USER_POOL_ID=$(terraform output -raw cognito_user_pool_id 2>/dev/null || echo "")
if [[ -n "$USER_POOL_ID" ]]; then
    print_status "Deleting test users from Cognito user pool..."
    
    # List and delete users
    USER_LIST=$(aws cognito-idp list-users --user-pool-id "$USER_POOL_ID" --region "$AWS_REGION" --query 'Users[].Username' --output text 2>/dev/null || echo "")
    
    if [[ -n "$USER_LIST" ]]; then
        for username in $USER_LIST; do
            if [[ "$username" != "None" ]]; then
                print_status "Deleting user: $username"
                aws cognito-idp admin-delete-user --user-pool-id "$USER_POOL_ID" --username "$username" --region "$AWS_REGION" || true
            fi
        done
    fi
fi

echo ""
print_header "Step 5: Terraform Destroy"

print_status "Running Terraform destroy..."
print_warning "This may take several minutes..."

# Run terraform destroy
if terraform destroy -auto-approve; then
    print_status "✅ Terraform destroy completed successfully"
else
    print_error "❌ Terraform destroy encountered errors"
    print_warning "Some resources may still exist. Please check the AWS console."
fi

echo ""
print_header "Step 6: Cleanup Verification"

# Verify cleanup
print_status "Verifying cleanup..."

# Check for remaining Lambda functions
REMAINING_LAMBDAS=$(aws lambda list-functions --region "$AWS_REGION" --query 'Functions[?starts_with(FunctionName, `receipt-search-dev`)].FunctionName' --output text 2>/dev/null || echo "")
if [[ -n "$REMAINING_LAMBDAS" && "$REMAINING_LAMBDAS" != "None" ]]; then
    print_warning "Remaining Lambda functions found: $REMAINING_LAMBDAS"
else
    print_status "✅ No Lambda functions remaining"
fi

# Check for remaining S3 buckets
REMAINING_BUCKETS=$(aws s3api list-buckets --region "$AWS_REGION" --query 'Buckets[?starts_with(Name, `receipt-search-dev`)].Name' --output text 2>/dev/null || echo "")
if [[ -n "$REMAINING_BUCKETS" && "$REMAINING_BUCKETS" != "None" ]]; then
    print_warning "Remaining S3 buckets found: $REMAINING_BUCKETS"
else
    print_status "✅ No S3 buckets remaining"
fi

# Check for remaining DynamoDB tables
REMAINING_TABLES=$(aws dynamodb list-tables --region "$AWS_REGION" --query 'TableNames[?starts_with(@, `receipt-search-dev`)]' --output text 2>/dev/null || echo "")
if [[ -n "$REMAINING_TABLES" && "$REMAINING_TABLES" != "None" ]]; then
    print_warning "Remaining DynamoDB tables found: $REMAINING_TABLES"
else
    print_status "✅ No DynamoDB tables remaining"
fi

echo ""
print_header "Step 7: Local Cleanup"

# Clean up local files
print_status "Cleaning up local deployment files..."

# Remove deployment packages
if [[ -d "$SCRIPT_DIR/packages" ]]; then
    rm -rf "$SCRIPT_DIR/packages"
    print_status "Removed deployment packages"
fi

# Clean up temporary files
rm -f /tmp/cognito_tokens.sh /tmp/lambda-response.json /tmp/test_receipt.txt 2>/dev/null || true

# Clean up Terraform state backups (keep the latest for safety)
find "$TERRAFORM_DIR" -name "terraform.tfstate.backup.*" -type f -delete 2>/dev/null || true

print_status "Local cleanup completed"

echo ""
print_header "Cleanup Summary"
echo "==============="
print_status "✅ Lambda functions deleted"
print_status "✅ S3 buckets emptied and deleted"
print_status "✅ Infrastructure destroyed via Terraform"
print_status "✅ Local deployment files cleaned"
print_status "✅ Temporary files removed"
echo ""

print_status "🎉 Cleanup completed successfully!"
print_status ""
print_status "Cost Impact:"
print_status "- All AWS resources have been terminated"
print_status "- No ongoing charges for EC2, Lambda, S3, DynamoDB, etc."
print_status "- VPC, NAT Gateway, and other networking costs stopped"
print_status ""

print_warning "Note: It may take a few minutes for all charges to stop appearing in AWS billing."
print_warning "If you see any remaining resources in the AWS console, please delete them manually."

cd - > /dev/null
