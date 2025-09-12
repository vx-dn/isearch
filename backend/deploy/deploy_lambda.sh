#!/bin/bash

# Lambda deployment script for Receipt Search Application
# This script packages and deploys Lambda functions to AWS

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$BACKEND_DIR")"
INFRASTRUCTURE_DIR="$PROJECT_ROOT/infrastructure"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="dev"
AWS_REGION="ap-southeast-1"
FUNCTION_NAME=""
DEPLOY_ALL=false
PACKAGE_ONLY=false

# Function to print colored output
print_info() {
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
    cat << EOF
Usage: $0 [OPTIONS]

Deploy Lambda functions for Receipt Search Application

OPTIONS:
    -e, --environment ENV    Environment (dev, staging, prod) [default: dev]
    -r, --region REGION      AWS region [default: ap-southeast-1]
    -f, --function NAME      Deploy specific function (api, image-processor, text-extractor, cleanup-worker)
    -a, --all               Deploy all functions
    -p, --package-only      Package only, don't deploy
    -h, --help              Show this help message

EXAMPLES:
    $0 --all                                    # Deploy all functions to dev
    $0 -f api -e prod                          # Deploy API function to production
    $0 --function image-processor --region us-west-2  # Deploy to specific region
    $0 --package-only --all                    # Package all functions without deploying

PREREQUISITES:
    1. AWS CLI configured with appropriate permissions
    2. Terraform infrastructure already deployed
    3. Python 3.10+ and pip installed
    4. ZIP utility available
EOF
}

# Function to get Terraform outputs
get_terraform_outputs() {
    local tf_dir="$INFRASTRUCTURE_DIR/terraform"
    
    if [[ ! -f "$tf_dir/terraform.tfstate" ]]; then
        print_error "Terraform state not found. Please deploy infrastructure first."
        exit 1
    fi
    
    cd "$tf_dir"
    
    # Set AWS region from Terraform outputs if not specified
    if [[ -z "$AWS_REGION" ]]; then
        local api_url=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")
        if [[ "$api_url" =~ ap-southeast-1 ]]; then
            AWS_REGION="ap-southeast-1"
        elif [[ "$api_url" =~ us-east-1 ]]; then
            AWS_REGION="us-east-1"
        elif [[ "$api_url" =~ us-west-2 ]]; then
            AWS_REGION="us-west-2"
        else
            AWS_REGION="us-east-1"  # fallback
        fi
        print_info "Detected AWS region: $AWS_REGION"
    fi
    
    # Extract required outputs
    API_GATEWAY_ID=$(terraform output -raw api_gateway_id 2>/dev/null || echo "")
    API_GATEWAY_URL=$(terraform output -raw api_gateway_url 2>/dev/null || echo "")
    RECEIPTS_TABLE=$(terraform output -raw receipts_table_name 2>/dev/null || echo "")
    USERS_TABLE=$(terraform output -raw users_table_name 2>/dev/null || echo "")
    RECEIPTS_BUCKET=$(terraform output -raw receipts_bucket_name 2>/dev/null || echo "")
    PROCESSING_QUEUE_URL=$(terraform output -raw processing_queue_url 2>/dev/null || echo "")
    LAMBDA_EXECUTION_ROLE=$(terraform output -raw lambda_execution_role_arn 2>/dev/null || echo "")
    IMAGE_PROCESSOR_ROLE=$(terraform output -raw image_processor_role_arn 2>/dev/null || echo "")
    TEXT_EXTRACTOR_ROLE=$(terraform output -raw text_extractor_role_arn 2>/dev/null || echo "")
    LAMBDA_SECURITY_GROUP=$(terraform output -raw lambda_security_group_id 2>/dev/null || echo "")
    VPC_ID=$(terraform output -raw vpc_id 2>/dev/null || echo "")
    MEILISEARCH_PRIVATE_IP=$(terraform output -raw meilisearch_private_ip 2>/dev/null || echo "")
    COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id 2>/dev/null || echo "")
    COGNITO_CLIENT_ID=$(terraform output -raw cognito_user_pool_client_id 2>/dev/null || echo "")
    
    # Construct subnet IDs (we'll need to query these)
    PRIVATE_SUBNET_ID=$(aws ec2 describe-subnets \
        --filters "Name=vpc-id,Values=$VPC_ID" "Name=tag:Type,Values=private" \
        --query 'Subnets[0].SubnetId' --output text --region "$AWS_REGION" 2>/dev/null || echo "")
    
    cd "$SCRIPT_DIR"
}

# Function to create deployment package
create_deployment_package() {
    local function_name=$1
    local package_dir="$SCRIPT_DIR/packages/${function_name}"
    local zip_file="$SCRIPT_DIR/packages/${function_name}.zip"
    
    print_info "Creating deployment package for $function_name" >&2
    
    # Clean up previous package
    rm -rf "$package_dir"
    rm -f "$zip_file"
    mkdir -p "$package_dir"
    
    # Copy Lambda function code
    cp "$SCRIPT_DIR/lambda_functions.py" "$package_dir/"
    
    # Copy source code
    cp -r "$BACKEND_DIR/src" "$package_dir/"
    
    # Install dependencies
    if [[ -f "$SCRIPT_DIR/requirements-lambda.txt" ]]; then
        print_info "Installing Python dependencies" >&2
        pip install -r "$SCRIPT_DIR/requirements-lambda.txt" -t "$package_dir" --quiet --no-warn-script-location
    fi
    
    # Create ZIP package
    cd "$package_dir"
    zip -r "../$(basename "$zip_file")" . -q
    cd "$SCRIPT_DIR"
    
    print_info "Package created: $zip_file" >&2
    # Return the zip file path cleanly
    echo "$zip_file"
}

# Function to deploy a Lambda function
deploy_function() {
    local function_name=$1
    local handler=$2
    local timeout=$3
    local memory=$4
    
    print_info "Deploying Lambda function: $function_name"
    
    # Create deployment package
    local zip_file=$(create_deployment_package "$function_name")
    
    if [[ ! -f "$zip_file" ]]; then
        print_error "Failed to create deployment package for $function_name"
        return 1
    fi
    
    # Deploy or update function
    if aws lambda get-function --function-name "$function_name" --region "$AWS_REGION" >/dev/null 2>&1; then
        print_info "Updating existing function: $function_name"
        aws lambda update-function-code 
            --function-name "$function_name" 
            --zip-file "fileb://$zip_file" 
            --region "$AWS_REGION" >/dev/null 2>&1
        
        aws lambda update-function-configuration 
            --function-name "$function_name" 
            --timeout "$timeout" 
            --memory-size "$memory" 
            --region "$AWS_REGION" >/dev/null 2>&1
    else
        print_info "Creating new function: $function_name"
        aws lambda create-function 
            --function-name "$function_name" 
            --runtime python3.10 
            --role "$LAMBDA_ROLE_ARN" 
            --handler "$handler" 
            --zip-file "fileb://$zip_file" 
            --timeout "$timeout" 
            --memory-size "$memory" 
            --region "$AWS_REGION" >/dev/null 2>&1
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "Successfully deployed: $function_name"
    else
        print_error "Failed to deploy: $function_name"
        return 1
    fi
}

# Function to deploy Lambda function
deploy_lambda_function() {
    local function_name=$1
    local handler=$2
    local role_arn=$3
    local zip_file=$4
    local timeout=${5:-30}
    local memory=${6:-512}
    
    local full_function_name="${PROJECT_NAME}-${ENVIRONMENT}-${function_name}"
    
    print_info "Deploying Lambda function: $full_function_name"
    
    # Check if function exists
    if aws lambda get-function --function-name "$full_function_name" --region "$AWS_REGION" &>/dev/null; then
        print_info "Updating existing function: $full_function_name"
        
        # Update function code
        aws lambda update-function-code \
            --function-name "$full_function_name" \
            --zip-file "fileb://$zip_file" \
            --region "$AWS_REGION" > /dev/null
        
        # Update function configuration
        aws lambda update-function-configuration \
            --function-name "$full_function_name" \
            --handler "$handler" \
            --runtime "python3.10" \
            --timeout "$timeout" \
            --memory-size "$memory" \
            --environment "Variables={
                RECEIPTS_TABLE=$RECEIPTS_TABLE,
                USERS_TABLE=$USERS_TABLE,
                RECEIPTS_BUCKET=$RECEIPTS_BUCKET,
                PROCESSING_QUEUE_URL=$PROCESSING_QUEUE_URL,
                MEILISEARCH_URL=http://$MEILISEARCH_PRIVATE_IP:7700,
                MEILISEARCH_KEY=$MEILISEARCH_MASTER_KEY,
                COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID,
                COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID,
                ENVIRONMENT=$ENVIRONMENT
            }" \
            --region "$AWS_REGION" > /dev/null
        
    else
        print_info "Creating new function: $full_function_name"
        
        # Determine VPC configuration
        local vpc_config=""
        if [[ "$function_name" != "api" ]]; then
            vpc_config="--vpc-config SubnetIds=[$PRIVATE_SUBNET_ID],SecurityGroupIds=[$LAMBDA_SECURITY_GROUP]"
        fi
        
        # Create function
        aws lambda create-function \
            --function-name "$full_function_name" \
            --runtime "python3.10" \
            --role "$role_arn" \
            --handler "$handler" \
            --zip-file "fileb://$zip_file" \
            --timeout "$timeout" \
            --memory-size "$memory" \
            --environment "Variables={
                RECEIPTS_TABLE=$RECEIPTS_TABLE,
                USERS_TABLE=$USERS_TABLE,
                RECEIPTS_BUCKET=$RECEIPTS_BUCKET,
                PROCESSING_QUEUE_URL=$PROCESSING_QUEUE_URL,
                MEILISEARCH_URL=http://$MEILISEARCH_PRIVATE_IP:7700,
                MEILISEARCH_KEY=$MEILISEARCH_MASTER_KEY,
                COGNITO_USER_POOL_ID=$COGNITO_USER_POOL_ID,
                COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID,
                ENVIRONMENT=$ENVIRONMENT
            }" \
            $vpc_config \
            --region "$AWS_REGION" > /dev/null
    fi
    
    print_info "Successfully deployed: $full_function_name"
}

# Function to configure API Gateway integration
configure_api_gateway() {
    local api_function_name="${PROJECT_NAME}-${ENVIRONMENT}-api"
    
    print_info "Configuring API Gateway integration"
    
    # Add permission for API Gateway to invoke Lambda
    aws lambda add-permission \
        --function-name "$api_function_name" \
        --statement-id "api-gateway-invoke" \
        --action "lambda:InvokeFunction" \
        --principal "apigateway.amazonaws.com" \
        --source-arn "arn:aws:execute-api:$AWS_REGION:*:$API_GATEWAY_ID/*/*" \
        --region "$AWS_REGION" &>/dev/null || true
    
    print_info "API Gateway integration configured"
}

# Function to configure S3 trigger
configure_s3_trigger() {
    local function_name="${PROJECT_NAME}-${ENVIRONMENT}-image-processor"
    
    print_info "Configuring S3 trigger for image processor"
    
    # Add permission for S3 to invoke Lambda
    aws lambda add-permission \
        --function-name "$function_name" \
        --statement-id "s3-trigger" \
        --action "lambda:InvokeFunction" \
        --principal "s3.amazonaws.com" \
        --source-arn "arn:aws:s3:::$RECEIPTS_BUCKET" \
        --region "$AWS_REGION" &>/dev/null || true
    
    # Configure S3 bucket notification (this might need to be done via Terraform)
    print_warning "S3 bucket notification should be configured via Terraform"
}

# Function to configure SQS trigger
configure_sqs_trigger() {
    local function_name="${PROJECT_NAME}-${ENVIRONMENT}-text-extractor"
    
    print_info "Configuring SQS trigger for text extractor"
    
    # Create event source mapping
    aws lambda create-event-source-mapping \
        --function-name "$function_name" \
        --event-source-arn "${PROCESSING_QUEUE_URL/https:\/\/sqs\.$AWS_REGION\.amazonaws\.com\/[0-9]*\//arn:aws:sqs:$AWS_REGION::}" \
        --batch-size 10 \
        --region "$AWS_REGION" &>/dev/null || true
    
    print_info "SQS trigger configured"
}

# Main deployment function
deploy_functions() {
    # Create packages directory
    mkdir -p "$SCRIPT_DIR/packages"
    
    # Set project name from Terraform outputs or default
    PROJECT_NAME="receipt-search"
    
    if [[ "$DEPLOY_ALL" == true ]] || [[ "$FUNCTION_NAME" == "api" ]]; then
        local zip_file=$(create_deployment_package "api")
        if [[ "$PACKAGE_ONLY" == false ]]; then
            deploy_lambda_function "api" "lambda_functions.api_handler" "$LAMBDA_EXECUTION_ROLE" "$zip_file" 30 512
            configure_api_gateway
        fi
    fi
    
    if [[ "$DEPLOY_ALL" == true ]] || [[ "$FUNCTION_NAME" == "image-processor" ]]; then
        local zip_file=$(create_deployment_package "image-processor")
        if [[ "$PACKAGE_ONLY" == false ]]; then
            deploy_lambda_function "image-processor" "lambda_functions.image_processor_handler" "$IMAGE_PROCESSOR_ROLE" "$zip_file" 60 1024
            configure_s3_trigger
        fi
    fi
    
    if [[ "$DEPLOY_ALL" == true ]] || [[ "$FUNCTION_NAME" == "text-extractor" ]]; then
        local zip_file=$(create_deployment_package "text-extractor")
        if [[ "$PACKAGE_ONLY" == false ]]; then
            deploy_lambda_function "text-extractor" "lambda_functions.text_extractor_handler" "$TEXT_EXTRACTOR_ROLE" "$zip_file" 300 2048
            configure_sqs_trigger
        fi
    fi
    
    if [[ "$DEPLOY_ALL" == true ]] || [[ "$FUNCTION_NAME" == "cleanup-worker" ]]; then
        local zip_file=$(create_deployment_package "cleanup-worker")
        if [[ "$PACKAGE_ONLY" == false ]]; then
            deploy_lambda_function "cleanup-worker" "lambda_functions.cleanup_worker_handler" "$LAMBDA_EXECUTION_ROLE" "$zip_file" 900 512
        fi
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -f|--function)
            FUNCTION_NAME="$2"
            shift 2
            ;;
        -a|--all)
            DEPLOY_ALL=true
            shift
            ;;
        -p|--package-only)
            PACKAGE_ONLY=true
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

# Validate arguments
if [[ "$DEPLOY_ALL" == false ]] && [[ -z "$FUNCTION_NAME" ]]; then
    print_error "Must specify either --all or --function"
    show_usage
    exit 1
fi

if [[ -n "$FUNCTION_NAME" ]] && [[ ! "$FUNCTION_NAME" =~ ^(api|image-processor|text-extractor|cleanup-worker)$ ]]; then
    print_error "Invalid function name. Must be one of: api, image-processor, text-extractor, cleanup-worker"
    exit 1
fi

# Main execution
print_info "Starting Lambda deployment for environment: $ENVIRONMENT"
print_info "AWS Region: $AWS_REGION"

# Check prerequisites
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install and configure it."
    exit 1
fi

if ! command -v zip &> /dev/null; then
    print_error "ZIP utility not found. Please install it."
    exit 1
fi

if ! aws sts get-caller-identity &>/dev/null; then
    print_error "AWS credentials not configured properly."
    exit 1
fi

# Get Terraform outputs
get_terraform_outputs

# Validate required outputs
if [[ -z "$LAMBDA_EXECUTION_ROLE" ]]; then
    print_error "Lambda execution role not found. Please ensure Terraform infrastructure is deployed."
    exit 1
fi

# Deploy functions
deploy_functions

print_info "Lambda deployment completed successfully!"

if [[ "$PACKAGE_ONLY" == false ]]; then
    print_info ""
    print_info "Next steps:"
    print_info "1. Test the API endpoints"
    print_info "2. Upload a test receipt image"
    print_info "3. Check CloudWatch logs for any issues"
    print_info ""
    print_info "API Gateway URL: https://$API_GATEWAY_ID.execute-api.$AWS_REGION.amazonaws.com/$ENVIRONMENT"
fi
