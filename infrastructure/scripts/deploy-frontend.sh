#!/bin/bash

# Frontend Deployment Script for Receipt Search Application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
AWS_REGION="ap-southeast-1"
ENVIRONMENT="dev"

# Help function
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Deploy the Vue.js frontend to AWS S3 and CloudFront"
    echo ""
    echo "Options:"
    echo "  -e, --env ENVIRONMENT    Environment to deploy to (default: dev)"
    echo "  -r, --region REGION      AWS region (default: ap-southeast-1)"
    echo "  -h, --help              Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                      # Deploy to dev environment"
    echo "  $0 -e prod             # Deploy to production"
    echo "  $0 -e staging -r us-east-1  # Deploy to staging in us-east-1"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--env)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -r|--region)
            AWS_REGION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option $1"
            show_help
            exit 1
            ;;
    esac
done

echo -e "${BLUE}🚀 Starting Frontend Deployment...${NC}"
echo -e "${BLUE}Environment: ${ENVIRONMENT}${NC}"
echo -e "${BLUE}AWS Region: ${AWS_REGION}${NC}"

# Check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    # Check if Node.js is installed
    if ! command -v node &> /dev/null; then
        echo -e "${RED}❌ Node.js is not installed${NC}"
        exit 1
    fi
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI is not installed${NC}"
        exit 1
    fi
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        echo -e "${RED}❌ Terraform is not installed${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Get Terraform outputs
get_terraform_outputs() {
    echo -e "${YELLOW}📊 Getting Terraform outputs...${NC}"
    
    cd infrastructure/terraform
    
    # Check if Terraform state exists
    if [ ! -f terraform.tfstate ]; then
        echo -e "${RED}❌ No Terraform state found. Please run 'terraform apply' first.${NC}"
        exit 1
    fi
    
    # Get outputs
    FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name 2>/dev/null || echo "")
    CLOUDFRONT_DISTRIBUTION_ID=$(terraform output -raw cloudfront_distribution_id 2>/dev/null || echo "")
    API_URL=$(terraform output -raw api_url 2>/dev/null || echo "")
    FRONTEND_URL=$(terraform output -raw frontend_url 2>/dev/null || echo "")
    
    if [ -z "$FRONTEND_BUCKET" ] || [ -z "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
        echo -e "${RED}❌ Required Terraform outputs not found. Make sure CloudFront module is deployed.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Terraform outputs retrieved${NC}"
    echo -e "  S3 Bucket: ${FRONTEND_BUCKET}"
    echo -e "  CloudFront ID: ${CLOUDFRONT_DISTRIBUTION_ID}"
    echo -e "  API URL: ${API_URL}"
    
    cd ../../
}

# Build frontend
build_frontend() {
    echo -e "${YELLOW}🏗️ Building frontend...${NC}"
    
    cd frontend
    
    # Install dependencies if node_modules doesn't exist
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}📦 Installing dependencies...${NC}"
        npm install
    fi
    
    # Create production environment file
    cat > .env.production << EOF
VITE_API_URL=${API_URL}
VITE_APP_NAME="Receipt Search"
VITE_APP_VERSION="$(git rev-parse HEAD 2>/dev/null || echo 'unknown')"
VITE_ENVIRONMENT=${ENVIRONMENT}
EOF
    
    # Build the application
    npm run build
    
    # Update health check file with build info
    BUILD_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    BUILD_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo 'unknown')
    
    sed -i "s/BUILD_TIMESTAMP/$BUILD_TIMESTAMP/g" dist/health.json
    sed -i "s/BUILD_COMMIT/$BUILD_COMMIT/g" dist/health.json
    sed -i "s/BUILD_ENVIRONMENT/$ENVIRONMENT/g" dist/health.json
    sed -i "s|API_URL|$API_URL|g" dist/health.json
    
    if [ ! -d "dist" ]; then
        echo -e "${RED}❌ Build failed - dist directory not created${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Frontend build completed${NC}"
    
    cd ../
}

# Deploy to S3
deploy_to_s3() {
    echo -e "${YELLOW}☁️ Deploying to S3...${NC}"
    
    # Sync files to S3
    aws s3 sync frontend/dist/ "s3://${FRONTEND_BUCKET}" \
        --region "${AWS_REGION}" \
        --delete \
        --cache-control "max-age=31536000" \
        --exclude "*.html" \
        --exclude "service-worker.js"
    
    # Upload HTML files with no-cache
    aws s3 sync frontend/dist/ "s3://${FRONTEND_BUCKET}" \
        --region "${AWS_REGION}" \
        --cache-control "no-cache, no-store, must-revalidate" \
        --include "*.html" \
        --include "service-worker.js"
    
    echo -e "${GREEN}✅ Files uploaded to S3${NC}"
}

# Invalidate CloudFront
invalidate_cloudfront() {
    echo -e "${YELLOW}🔄 Invalidating CloudFront cache...${NC}"
    
    INVALIDATION_ID=$(aws cloudfront create-invalidation \
        --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
        --paths "/*" \
        --query 'Invalidation.Id' \
        --output text \
        --region "${AWS_REGION}")
    
    echo -e "${GREEN}✅ CloudFront invalidation created: ${INVALIDATION_ID}${NC}"
    
    # Optional: Wait for invalidation to complete (uncomment if needed)
    # echo -e "${YELLOW}⏳ Waiting for invalidation to complete...${NC}"
    # aws cloudfront wait invalidation-completed \
    #     --distribution-id "${CLOUDFRONT_DISTRIBUTION_ID}" \
    #     --id "${INVALIDATION_ID}"
    # echo -e "${GREEN}✅ CloudFront invalidation completed${NC}"
}

# Main deployment function
main() {
    check_prerequisites
    get_terraform_outputs
    build_frontend
    deploy_to_s3
    invalidate_cloudfront
    
    echo ""
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo ""
    echo -e "${BLUE}📊 Deployment Summary:${NC}"
    echo -e "  Environment: ${ENVIRONMENT}"
    echo -e "  S3 Bucket: ${FRONTEND_BUCKET}"
    echo -e "  CloudFront Distribution: ${CLOUDFRONT_DISTRIBUTION_ID}"
    echo -e "  Frontend URL: ${FRONTEND_URL}"
    echo ""
    echo -e "${YELLOW}💡 Note: CloudFront cache invalidation may take up to 15 minutes to complete.${NC}"
    echo -e "${YELLOW}💡 You can monitor the invalidation progress in the AWS Console.${NC}"
}

# Run main function
main