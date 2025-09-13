# Lambda Functions - Complete Deployment Guide

**📍 Location**: `backend/deploy/`  
**📋 Status**: All functions deployed and operational  
**🔗 Overview**: See main `/README.md` for complete infrastructure overview

This guide covers Lambda function deployment, testing, and management for the Receipt Search Application.

## Available Scripts

- **`deploy_lambda.sh`** - Deploy Lambda functions
- **`test_deployment.sh`** - Test Lambda deployment
- **`test_pipeline.sh`** - End-to-end pipeline testing  
- **`test_auth.sh`** - Authentication testing
- **`stop_services.sh`** - Stop services to save costs (30-40% reduction)
- **`start_services.sh`** - Restart stopped services
- **`cleanup.sh`** - Development environment cleanup
- **`verify_cleanup.sh`** - Verify cleanup operations

## Prerequisites

1. **Infrastructure Deployed**: Terraform infrastructure must be deployed first
2. **AWS CLI**: Configured with appropriate permissions
3. **Python Dependencies**: Install required packages
4. **Environment Variables**: Set Meilisearch master key

## Quick Start

### 1. Set Environment Variables

```bash
# Required: Meilisearch master key (use the same one from infrastructure deployment)
export MEILISEARCH_MASTER_KEY="your-secure-master-key-here"

# Optional: Override defaults
export AWS_REGION="ap-southeast-1"  # Match your infrastructure region
```

### 2. Deploy All Lambda Functions

```bash
# Navigate to backend deploy directory
cd backend/deploy

# Deploy all functions to development environment
./deploy_lambda.sh --all

# Deploy to production environment
./deploy_lambda.sh --all --environment prod --region ap-southeast-1
```

### 3. Deploy Individual Functions

```bash
# Deploy only the API handler
./deploy_lambda.sh --function api

# Deploy image processor
./deploy_lambda.sh --function image-processor

# Deploy text extractor
./deploy_lambda.sh --function text-extractor

# Deploy cleanup worker
./deploy_lambda.sh --function cleanup-worker
```

## Deployment Commands

### Basic Deployment
```bash
# Deploy all functions
./deploy_lambda.sh --all

# Deploy specific function
./deploy_lambda.sh --function api
```

### Environment-Specific Deployment
```bash
# Deploy to staging
./deploy_lambda.sh --all --environment staging

# Deploy to production
./deploy_lambda.sh --all --environment prod
```

### Package Without Deploying
```bash
# Create deployment packages only (for testing/validation)
./deploy_lambda.sh --all --package-only
```

## Function Overview

### 1. API Handler (`api`)
- **Purpose**: Main REST API handler for all HTTP requests
- **Trigger**: API Gateway
- **Timeout**: 30 seconds
- **Memory**: 512 MB
- **Handler**: `lambda_functions.api_handler`

### 2. Image Processor (`image-processor`)
- **Purpose**: Process uploaded receipt images
- **Trigger**: S3 bucket uploads
- **Timeout**: 60 seconds
- **Memory**: 1024 MB
- **Handler**: `lambda_functions.image_processor_handler`

### 3. Text Extractor (`text-extractor`)
- **Purpose**: Extract text from images using AWS Textract
- **Trigger**: SQS messages
- **Timeout**: 300 seconds (5 minutes)
- **Memory**: 2048 MB
- **Handler**: `lambda_functions.text_extractor_handler`

### 4. Cleanup Worker (`cleanup-worker`)
- **Purpose**: Clean up expired receipts and files
- **Trigger**: CloudWatch Events (scheduled)
- **Timeout**: 900 seconds (15 minutes)
- **Memory**: 512 MB
- **Handler**: `lambda_functions.cleanup_worker_handler`

## Verification

### Check Function Status
```bash
# List all Lambda functions
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `receipt-search-dev-`)].{Name:FunctionName,Runtime:Runtime,Status:State}'

# Get specific function details
aws lambda get-function --function-name receipt-search-dev-api
```

### Test API Endpoint
```bash
# Get API Gateway URL from Terraform outputs
cd ../../infrastructure/terraform
API_URL=$(terraform output -raw api_gateway_url)

# Test health endpoint
curl "$API_URL/api/v1/health"
```

### Check Logs
```bash
# View API function logs
aws logs tail /aws/lambda/receipt-search-dev-api --follow

# View image processor logs
aws logs tail /aws/lambda/receipt-search-dev-image-processor --follow
```

## Troubleshooting

### Common Issues

1. **Permission Errors**
   ```bash
   # Check IAM role permissions
   aws iam get-role --role-name receipt-search-dev-lambda-execution-role
   ```

2. **VPC Configuration Issues**
   ```bash
   # Check VPC endpoints are accessible
   # Functions may timeout if VPC configuration is incorrect
   ```

3. **Package Size Too Large**
   ```bash
   # Lambda has a 50MB zipped package limit
   # Remove unnecessary dependencies from requirements-lambda.txt
   ```

4. **Environment Variables Missing**
   ```bash
   # Check function environment variables
   aws lambda get-function-configuration --function-name receipt-search-dev-api
   ```

### Debugging

1. **Enable Debug Logging**
   ```bash
   # Set log level to DEBUG in Lambda environment variables
   aws lambda update-function-configuration \
     --function-name receipt-search-dev-api \
     --environment Variables="{LOG_LEVEL=DEBUG,...}"
   ```

2. **Test Functions Locally**
   ```bash
   # Install dependencies locally
   pip install -r requirements-lambda.txt
   
   # Run unit tests
   python -m pytest ../tests/
   ```

## Security Considerations

1. **Environment Variables**: Never hardcode secrets in Lambda code
2. **IAM Roles**: Each function uses least-privilege IAM roles
3. **VPC**: Non-API functions run in private subnets
4. **Encryption**: All data encrypted in transit and at rest

## Cost Optimization

1. **Memory Allocation**: Right-sized for each function's needs
2. **Timeout Settings**: Conservative but not excessive
3. **Cold Start**: API function stays warm with reserved concurrency
4. **Monitoring**: CloudWatch alarms for cost anomalies

## Next Steps

After successful deployment:

1. **Configure Frontend**: Update API endpoints in frontend configuration
2. **Set Up Monitoring**: Create CloudWatch dashboards
3. **Load Testing**: Test with realistic traffic patterns
4. **CI/CD Pipeline**: Automate deployments from git commits
