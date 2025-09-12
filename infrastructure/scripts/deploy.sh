#!/bin/bash

# Receipt Search Application Infrastructure Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="$SCRIPT_DIR/../terraform"

# Default values
ENVIRONMENT="dev"
ACTION="plan"
AUTO_APPROVE=false

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -e, --environment ENVIRONMENT    Environment to deploy (dev, staging, prod). Default: dev"
    echo "  -a, --action ACTION             Terraform action (plan, apply, destroy). Default: plan"
    echo "  -y, --auto-approve              Auto approve terraform apply/destroy"
    echo "  -h, --help                      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 -e dev -a plan                # Plan deployment for dev environment"
    echo "  $0 -e dev -a apply -y            # Apply deployment for dev environment with auto-approve"
    echo "  $0 -e prod -a destroy            # Destroy prod environment (with confirmation)"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -a|--action)
            ACTION="$2"
            shift 2
            ;;
        -y|--auto-approve)
            AUTO_APPROVE=true
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT. Must be dev, staging, or prod."
    exit 1
fi

# Validate action
if [[ ! "$ACTION" =~ ^(plan|apply|destroy|init|validate)$ ]]; then
    print_error "Invalid action: $ACTION. Must be plan, apply, destroy, init, or validate."
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    print_error "Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install and configure AWS CLI first."
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    print_error "AWS credentials not configured or invalid. Please configure AWS CLI first."
    exit 1
fi

# Check for required environment variables
if [[ "$ACTION" == "apply" || "$ACTION" == "plan" ]]; then
    if [[ -z "$TF_VAR_meilisearch_master_key" ]]; then
        print_warning "TF_VAR_meilisearch_master_key environment variable is not set."
        read -s -p "Please enter Meilisearch master key: " MASTER_KEY
        echo
        export TF_VAR_meilisearch_master_key="$MASTER_KEY"
    fi
fi

# Change to terraform directory
cd "$TERRAFORM_DIR"

print_status "Starting Terraform $ACTION for environment: $ENVIRONMENT"

# Initialize Terraform if needed
if [[ ! -d ".terraform" ]] || [[ "$ACTION" == "init" ]]; then
    print_status "Initializing Terraform..."
    terraform init
fi

# Validate Terraform configuration
if [[ "$ACTION" == "validate" ]]; then
    print_status "Validating Terraform configuration..."
    terraform validate
    print_status "Terraform configuration is valid."
    exit 0
fi

# Set up terraform command with var file
TERRAFORM_CMD="terraform $ACTION -var-file=environments/${ENVIRONMENT}.tfvars"

# Add auto-approve flag if requested and action is apply or destroy
if [[ "$AUTO_APPROVE" == true ]] && [[ "$ACTION" =~ ^(apply|destroy)$ ]]; then
    TERRAFORM_CMD="$TERRAFORM_CMD -auto-approve"
fi

# Special handling for destroy action
if [[ "$ACTION" == "destroy" ]] && [[ "$AUTO_APPROVE" == false ]]; then
    print_warning "You are about to destroy the $ENVIRONMENT environment!"
    print_warning "This action cannot be undone and will delete all resources."
    read -p "Are you sure you want to continue? (type 'yes' to confirm): " confirm
    if [[ "$confirm" != "yes" ]]; then
        print_status "Destroy cancelled."
        exit 0
    fi
fi

# Execute terraform command
print_status "Executing: $TERRAFORM_CMD"
eval $TERRAFORM_CMD

TERRAFORM_EXIT_CODE=$?

if [[ $TERRAFORM_EXIT_CODE -eq 0 ]]; then
    print_status "Terraform $ACTION completed successfully!"
    
    # Show outputs for plan and apply
    if [[ "$ACTION" =~ ^(plan|apply)$ ]]; then
        print_status "Infrastructure outputs:"
        terraform output
    fi
else
    print_error "Terraform $ACTION failed with exit code: $TERRAFORM_EXIT_CODE"
    exit $TERRAFORM_EXIT_CODE
fi

# Post-deployment information
if [[ "$ACTION" == "apply" ]]; then
    print_status "Deployment completed successfully!"
    print_status "Next steps:"
    echo "  1. Wait for EC2 instance to fully initialize (5-10 minutes)"
    echo "  2. Deploy Lambda functions using the backend deployment scripts"
    echo "  3. Test the API endpoints"
    echo ""
    print_status "Useful commands:"
    echo "  - View outputs: terraform output"
    echo "  - Check Meilisearch health: ssh to EC2 and curl http://localhost:7700/health"
    echo "  - View logs: Check CloudWatch logs for Lambda functions"
fi
