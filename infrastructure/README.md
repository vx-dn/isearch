# Receipt Search Application Infrastructure

This directory contains the Terraform infrastructure code for the Receipt Search Application, a serverless receipt management system built on AWS.

## Architecture Overview

The infrastructure includes:

- **AWS Lambda Functions**: API handler, image processor, text extractor, and cleanup worker
- **Amazon S3**: Receipt storage with lifecycle policies
- **Amazon DynamoDB**: Metadata storage for receipts and users
- **Amazon SQS**: Asynchronous processing queue with dead letter queue
- **AWS Cognito**: User authentication and authorization
- **AWS Textract**: OCR text extraction from receipt images
- **EC2 + Meilisearch**: Search engine for receipt content
- **API Gateway**: RESTful API endpoint
- **VPC**: Secure networking with private/public subnets

## Prerequisites

1. **AWS CLI**: Installed and configured with appropriate credentials
2. **Terraform**: Version >= 1.0 installed
3. **Proper IAM permissions**: Your AWS user/role needs permissions to create the required resources

## Quick Start

### 1. Set Environment Variables

```bash
# Required: Meilisearch master key
export TF_VAR_meilisearch_master_key="your-secure-master-key-here"

# Optional: Override default values
export TF_VAR_aws_region="ap-southeast-1"
export TF_VAR_environment="dev"
```

### 2. Deploy Infrastructure

```bash
# Navigate to scripts directory
cd infrastructure/scripts

# Plan deployment (review changes)
./deploy.sh -e dev -a plan

# Apply deployment
./deploy.sh -e dev -a apply -y
```

### 3. Verify Deployment

After deployment (5-10 minutes for EC2 to initialize):

```bash
# Check Terraform outputs
cd ../terraform
terraform output

# Verify AWS resources in the console
# Check Meilisearch health (via EC2 Systems Manager or SSH)
```

## Directory Structure

```
infrastructure/
├── terraform/
│   ├── main.tf                 # Main Terraform configuration
│   ├── variables.tf            # Global variables
│   ├── outputs.tf             # Infrastructure outputs
│   ├── modules/               # Terraform modules
│   │   ├── s3/               # S3 buckets and policies
│   │   ├── dynamodb/         # DynamoDB tables
│   │   ├── sqs/              # SQS queues
│   │   ├── cognito/          # Authentication
│   │   ├── iam/              # IAM roles and policies
│   │   ├── vpc/              # Networking
│   │   ├── ec2/              # Meilisearch server
│   │   └── api_gateway/      # API Gateway
│   └── environments/
│       └── dev.tfvars        # Environment-specific variables
└── scripts/
    └── deploy.sh             # Deployment automation script
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TF_VAR_meilisearch_master_key` | Meilisearch authentication key | - | Yes |
| `TF_VAR_aws_region` | AWS region | ap-southeast-1 | No |
| `TF_VAR_environment` | Environment name | dev | No |
| `TF_VAR_free_user_image_quota` | Free user image limit | 50 | No |
| `TF_VAR_paid_user_image_quota` | Paid user image limit | 1000 | No |

### Customizing Environments

Create new `.tfvars` files in `environments/` directory:

```bash
# environments/prod.tfvars
environment = "prod"
aws_region = "ap-southeast-1"
free_user_image_quota = 50
paid_user_image_quota = 1000
cognito_domain_prefix = "receipt-search-prod"
```

## Deployment Commands

### Basic Operations

```bash
# Plan changes
./deploy.sh -e dev -a plan

# Apply changes
./deploy.sh -e dev -a apply

# Destroy infrastructure
./deploy.sh -e dev -a destroy

# Initialize Terraform
./deploy.sh -e dev -a init

# Validate configuration
./deploy.sh -e dev -a validate
```

### Advanced Options

```bash
# Auto-approve apply/destroy
./deploy.sh -e dev -a apply -y

# Deploy to production
./deploy.sh -e prod -a apply

# Plan with custom variables
TF_VAR_custom_var="value" ./deploy.sh -e dev -a plan
```

## Key Resources Created

### Storage
- **S3 Bucket**: Receipt images and thumbnails
- **DynamoDB Tables**: Receipts, users, and configuration
- **EBS Volume**: Meilisearch data storage

### Compute
- **Lambda Functions**: API processing and background jobs
- **EC2 Instance**: Meilisearch search engine (t3.micro)

### Networking
- **VPC**: Isolated network environment
- **Subnets**: Public (NAT) and private (EC2/Lambda)
- **Security Groups**: Restricted access rules
- **VPC Endpoints**: Cost-optimized AWS service access

### Security
- **IAM Roles**: Least-privilege access for services
- **Cognito User Pool**: User authentication
- **S3 Encryption**: Server-side encryption enabled
- **VPC Security**: Private subnet isolation

## Cost Optimization

The infrastructure is designed for AWS Free Tier eligibility:

- **EC2**: t3.micro instance (12 months free)
- **Lambda**: 1M requests/month free
- **DynamoDB**: On-demand pricing with free tier
- **S3**: 5GB storage free tier
- **API Gateway**: 1M API calls/month free

Estimated monthly cost after free tier: $15-30 for moderate usage.

## Monitoring and Logging

### CloudWatch Alarms
- API Gateway 4xx/5xx errors
- Lambda function errors and duration
- SQS dead letter queue messages
- EC2 instance health checks

### Log Groups
- API Gateway access logs
- Lambda function logs
- Meilisearch application logs

### Health Checks
- Automated Meilisearch health monitoring
- EC2 instance status checks
- Lambda function metrics

## Backup and Disaster Recovery

### Automated Backups
- **DynamoDB**: Point-in-time recovery enabled
- **Meilisearch**: Daily dumps to S3 (30-day retention)
- **S3**: Versioning enabled

### Recovery Procedures
1. **Meilisearch**: Restore from S3 backup dump
2. **DynamoDB**: Point-in-time recovery or manual backup
3. **S3**: Object versioning for accidental deletions

## Security Considerations

### Network Security
- Private subnets for sensitive resources
- Security groups with minimal required access
- VPC endpoints to avoid internet traffic

### Data Security
- Encryption at rest for all storage services
- IAM least-privilege access policies
- Cognito for secure user authentication

### Secrets Management
- Meilisearch key via environment variables
- Private keys stored in AWS Secrets Manager
- No hardcoded credentials in code

## Troubleshooting

### Common Issues

**1. Terraform State Lock**
```bash
# If deployment fails with state lock error
terraform force-unlock <LOCK_ID>
```

**2. Meilisearch Connection Issues**
```bash
# Check EC2 instance logs
aws logs get-log-events --log-group-name "/aws/ec2/meilisearch"

# SSH to instance and check Docker
sudo docker ps
sudo docker logs meilisearch
```

**3. Lambda Timeout Issues**
- Check CloudWatch logs for the specific function
- Verify VPC endpoints are working
- Check security group rules

**4. Cognito Configuration**
- Verify domain prefix is globally unique
- Check callback URLs match your frontend

### Getting Help

1. Check CloudWatch logs for detailed error messages
2. Review Terraform plan output for resource conflicts
3. Verify AWS service limits and quotas
4. Check IAM permissions for your deployment user

## Next Steps

After infrastructure deployment:

1. **Deploy Lambda Functions**: Use the backend deployment scripts
   ```bash
   # Set Meilisearch master key (use same key from infrastructure deployment)
   export MEILISEARCH_MASTER_KEY="your-secure-master-key-here"
   
   # Deploy all Lambda functions
   cd ../backend/deploy
   ./deploy_lambda.sh --all
   
   # Verify deployment
   aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `receipt-search-dev-`)].FunctionName'
   ```

2. **Test API Endpoints**: Verify the deployment works
   ```bash
   # Get API URL
   cd ../../infrastructure/terraform
   API_URL=$(terraform output -raw api_gateway_url)
   
   # Test health endpoint
   curl "$API_URL/api/v1/health"
   ```

3. **Configure Frontend**: Update API endpoints and Cognito settings
4. **Set Up CI/CD**: Configure automated deployments
5. **Load Test**: Verify performance under expected load
6. **Monitor**: Set up alerts and monitoring dashboards

## Contributing

When modifying infrastructure:

1. Always run `terraform plan` before applying changes
2. Test changes in dev environment first
3. Update documentation for any new resources
4. Follow security best practices
5. Consider cost implications of changes
