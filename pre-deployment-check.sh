#!/bin/bash

# Pre-deployment check script for Receipt Search Application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

echo "🚀 Receipt Search Application - Pre-deployment Check"
echo "=================================================="

# Check if we're in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    print_status "Virtual environment active: $VIRTUAL_ENV"
else
    print_warning "No virtual environment detected. Activating..."
    if [[ -f "../.venv/bin/activate" ]]; then
        source ../.venv/bin/activate
        print_status "Virtual environment activated"
    else
        print_error "Virtual environment not found. Please run from receipt-search-app directory."
        exit 1
    fi
fi

# Check Terraform
echo ""
echo "📦 Checking Terraform..."
if command -v terraform &> /dev/null; then
    TERRAFORM_VERSION=$(terraform version | head -n1 | grep -o 'v[0-9]\+\.[0-9]\+\.[0-9]\+' | sed 's/v//')
    print_status "Terraform installed: v$TERRAFORM_VERSION"
    
    if [[ $(echo "$TERRAFORM_VERSION 1.0.0" | tr " " "\n" | sort -V | head -n1) == "1.0.0" ]]; then
        print_status "Terraform version meets requirements (>= 1.0)"
    else
        print_error "Terraform version too old. Please upgrade to >= 1.0"
        exit 1
    fi
else
    print_error "Terraform not found. Please install Terraform first."
    exit 1
fi

# Check AWS CLI
echo ""
echo "☁️  Checking AWS CLI..."
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version 2>&1 | cut -d/ -f2 | cut -d' ' -f1)
    print_status "AWS CLI installed: v$AWS_VERSION"
else
    print_error "AWS CLI not found in virtual environment."
    exit 1
fi

# Check AWS credentials
echo ""
echo "🔐 Checking AWS credentials..."
if aws sts get-caller-identity &> /dev/null; then
    AWS_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
    AWS_USER=$(aws sts get-caller-identity --query 'Arn' --output text)
    AWS_REGION=$(aws configure get region || echo $AWS_DEFAULT_REGION)
    
    print_status "AWS Account: $AWS_ACCOUNT"
    print_status "AWS User/Role: $AWS_USER"
    print_status "AWS Region: $AWS_REGION"
else
    print_error "AWS credentials not configured or invalid."
    echo "Please run: aws configure"
    exit 1
fi

# Check required environment variables for deployment
echo ""
echo "🔑 Checking environment variables..."
if [[ -n "$TF_VAR_meilisearch_master_key" ]]; then
    print_status "Meilisearch master key is set"
else
    print_warning "TF_VAR_meilisearch_master_key not set"
    echo "   You'll need to set this before deployment:"
    echo "   export TF_VAR_meilisearch_master_key=\"your-secure-key-here\""
fi

# Check AWS service quotas (basic check)
echo ""
echo "📊 Checking AWS service availability..."

# Check if we can list S3 buckets (basic permission check)
if aws s3 ls &> /dev/null; then
    print_status "S3 access verified"
else
    print_warning "S3 access may be limited"
fi

# Check if we can describe EC2 instances (VPC permission check)
if aws ec2 describe-instances --max-items 1 &> /dev/null; then
    print_status "EC2/VPC access verified"
else
    print_warning "EC2/VPC access may be limited"
fi

# Check if we can list DynamoDB tables
if aws dynamodb list-tables &> /dev/null; then
    print_status "DynamoDB access verified"
else
    print_warning "DynamoDB access may be limited"
fi

echo ""
echo "🎯 Pre-deployment Summary:"
echo "========================"
print_status "Terraform ready"
print_status "AWS CLI configured"
print_status "Credentials valid"

if [[ -n "$TF_VAR_meilisearch_master_key" ]]; then
    print_status "Environment variables set"
    echo ""
    echo "✅ Ready for deployment!"
    echo ""
    echo "Next steps:"
    echo "1. cd infrastructure/scripts"
    echo "2. ./deploy.sh -e dev -a plan    # Review deployment plan"
    echo "3. ./deploy.sh -e dev -a apply -y # Deploy infrastructure"
else
    echo ""
    print_warning "Almost ready! Please set the Meilisearch master key:"
    echo "export TF_VAR_meilisearch_master_key=\"$(openssl rand -base64 32)\""
    echo ""
    echo "Then run this check again."
fi
