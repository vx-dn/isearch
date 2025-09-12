#!/bin/bash

# Test script for Lambda functions
# Verifies that deployed functions are working correctly

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRASTRUCTURE_DIR="$(dirname "$(dirname "$SCRIPT_DIR")")/infrastructure"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Get API Gateway URL from Terraform
get_api_url() {
    cd "$INFRASTRUCTURE_DIR/terraform"
    API_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")
    cd "$SCRIPT_DIR"
    
    if [[ -z "$API_URL" ]]; then
        print_error "Could not get API Gateway URL from Terraform outputs"
        exit 1
    fi
    
    echo "$API_URL"
}

# Test health endpoint
test_health_endpoint() {
    local api_url=$1
    
    print_info "Testing health endpoint: $api_url/api/v1/health"
    
    local response=$(curl -s -w "HTTPSTATUS:%{http_code}" "$api_url/api/v1/health" || echo "HTTPSTATUS:000")
    local body=$(echo "$response" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    local status=$(echo "$response" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')
    
    if [[ "$status" == "200" ]]; then
        print_success "Health endpoint is working"
        echo "Response: $body"
        return 0
    else
        print_error "Health endpoint failed (HTTP $status)"
        echo "Response: $body"
        return 1
    fi
}

# Test Lambda function exists
test_lambda_function_exists() {
    local function_name=$1
    
    print_info "Checking if Lambda function exists: $function_name"
    
    if aws lambda get-function --function-name "$function_name" &>/dev/null; then
        print_success "Lambda function exists: $function_name"
        
        # Get function status
        local state=$(aws lambda get-function --function-name "$function_name" --query 'Configuration.State' --output text)
        local last_update=$(aws lambda get-function --function-name "$function_name" --query 'Configuration.LastModified' --output text)
        
        echo "  State: $state"
        echo "  Last Updated: $last_update"
        return 0
    else
        print_error "Lambda function not found: $function_name"
        return 1
    fi
}

# Main test function
run_tests() {
    local environment=${1:-dev}
    local project_name="receipt-search"
    
    print_info "Starting tests for environment: $environment"
    print_info "================================"
    
    # Test API Gateway and health endpoint
    local api_url=$(get_api_url)
    test_health_endpoint "$api_url"
    
    echo ""
    
    # Test Lambda functions exist
    local functions=("api" "image-processor" "text-extractor" "cleanup-worker")
    local failed_tests=0
    
    for func in "${functions[@]}"; do
        local full_name="${project_name}-${environment}-${func}"
        if ! test_lambda_function_exists "$full_name"; then
            ((failed_tests++))
        fi
        echo ""
    done
    
    # Summary
    print_info "Test Summary"
    print_info "============"
    
    if [[ $failed_tests -eq 0 ]]; then
        print_success "All tests passed! 🎉"
        print_info ""
        print_info "Your Lambda functions are deployed and ready to use."
        print_info "API Gateway URL: $api_url"
    else
        print_error "$failed_tests test(s) failed"
        print_info ""
        print_info "Please check the deployment and try again."
        exit 1
    fi
}

# Parse arguments
ENVIRONMENT="dev"

while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Test deployed Lambda functions"
            echo ""
            echo "OPTIONS:"
            echo "  -e, --environment ENV    Environment to test [default: dev]"
            echo "  -h, --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check prerequisites
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install it."
    exit 1
fi

if ! command -v curl &> /dev/null; then
    print_error "curl not found. Please install it."
    exit 1
fi

if ! aws sts get-caller-identity &>/dev/null; then
    print_error "AWS credentials not configured properly."
    exit 1
fi

# Run tests
run_tests "$ENVIRONMENT"
