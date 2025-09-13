# Receipt Search App

A serverless receipt search application built with AWS Lambda, FastAPI, and Meilisearch for intelligent document processing and search.

## 🏗️ Architecture

- **Backend**: Python FastAPI with AWS Lambda
- **Search**: Meilisearch for full-text search
- **Authentication**: AWS Cognito
- **Storage**: S3 for files, DynamoDB for metadata
- **Processing**: AWS Textract for OCR
- **Infrastructure**: Terraform for AWS resources

## 🚀 Quick Start

### Prerequisites

- AWS CLI configured with appropriate permissions
- Terraform installed
- Python 3.10+
- GitHub Actions secrets configured (see below)

### Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/vx-dn/isearch.git
   cd isearch
   ```

2. **Setup environment variables**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your actual values (never commit this file!)
   ```

3. **Install dependencies**:
   ```bash
   # For development (includes testing, linting, etc.)
   pip install -r requirements-dev.txt
   
   # For production (runtime only)
   pip install -r requirements.txt
   ```

4. **Run tests**:
   ```bash
   pytest
   ```

### Important: Environment Variables Security

- **`.env`** files contain sensitive information and should **NEVER** be committed to git
- **`.env.example`** shows the required variables (safe to commit)
- Always copy `.env.example` to `.env` and modify with your actual values
- The `.gitignore` file ensures `.env` files are excluded from git

### Dependencies Structure

This project uses separate requirements files for different environments:

- **`requirements.txt`** - Runtime dependencies only (what the application imports)
- **`requirements-dev.txt`** - Development dependencies (testing, linting, formatting)
- **`requirements-prod.txt`** - Production optimizations (monitoring, WSGI servers)

**Benefits:**
- ✅ Smaller Docker images in production
- ✅ Faster deployment installs  
- ✅ Better security (fewer packages in production)
- ✅ Clear separation of concerns

### Deployment

#### Option 1: GitHub Actions (Recommended)

**Step 1: Configure GitHub Secrets**

Go to your GitHub repository → Settings → Secrets and variables → Actions and add:

```bash
# Required secrets:
AWS_ACCESS_KEY_ID           # Your AWS access key
AWS_SECRET_ACCESS_KEY       # Your AWS secret key  
MEILISEARCH_MASTER_KEY     # Generate: openssl rand -base64 32

# Optional (for staging/prod):
AWS_ACCESS_KEY_ID_STAGING
AWS_SECRET_ACCESS_KEY_STAGING
MEILISEARCH_MASTER_KEY_STAGING
AWS_ACCESS_KEY_ID_PROD
AWS_SECRET_ACCESS_KEY_PROD
MEILISEARCH_MASTER_KEY_PROD
```

**Step 2: Deploy via GitHub Actions**

**Option A - Manual Trigger (First deployment):**
1. Go to GitHub repository → Actions tab
2. Select "🔧 Hybrid Flexible CI/CD" workflow
3. Click "Run workflow" 
4. Configure options:
   - Environment: `dev`
   - Run tests: `true`
   - Deploy infrastructure: `true` (for first deployment)
5. Click "Run workflow"

**Option B - Automatic Trigger:**
- Push to `main` or `develop` branch
- Create pull request to `main`
- Workflow runs automatically with smart deployment detection

**Step 3: Monitor Deployment**
1. Watch the workflow execution in Actions tab
2. Check for any failures in individual jobs
3. View deployment logs for troubleshooting

#### Option 2: Manual Deployment

**Prerequisites:**
```bash
# Install required tools
aws --version          # AWS CLI v2
terraform --version    # Terraform >= 1.0
python --version       # Python 3.10+

# Configure AWS credentials
aws configure
# OR export AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
```

**Step 1: Deploy Infrastructure**
```bash
cd infrastructure/terraform

# Initialize Terraform
terraform init

# Review deployment plan
terraform plan -var-file=environments/dev.tfvars

# Deploy infrastructure (takes ~5-10 minutes)
terraform apply -var-file=environments/dev.tfvars

# Note the outputs (API Gateway URL, Cognito details, etc.)
terraform output
```

**Step 2: Set Environment Variables**
```bash
# Export Terraform outputs
export MEILISEARCH_MASTER_KEY="your_generated_key"
export COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
export COGNITO_CLIENT_ID=$(terraform output -raw cognito_client_id)
export API_GATEWAY_URL=$(terraform output -raw api_gateway_url)
```

**Step 3: Deploy Lambda Functions**
```bash
cd ../../backend/deploy

# Make scripts executable
chmod +x *.sh

# Deploy all Lambda functions
./deploy_lambda.sh

# Verify deployment
./test_deployment.sh
```

**Step 4: Test End-to-End**
```bash
# Test the complete pipeline
./test_pipeline.sh

# Test authentication
./test_auth.sh

# Check API health
curl $API_GATEWAY_URL/api/v1/health
```

#### Post-Deployment Verification

**Check Infrastructure:**
```bash
# Verify AWS resources
aws lambda list-functions --query 'Functions[?starts_with(FunctionName, `receipt-search-dev`)].FunctionName'
aws apigateway get-rest-apis --query 'items[?name==`receipt-search-dev-api`]'
aws ec2 describe-instances --filters "Name=tag:Name,Values=receipt-search-dev-meilisearch"

# Check Terraform state
cd infrastructure/terraform && terraform show
```

**Test API Endpoints:**
```bash
API_URL="https://your-api-id.execute-api.ap-southeast-1.amazonaws.com/dev"

# Health check
curl $API_URL/api/v1/health

# Create test user (replace with valid email)
aws cognito-idp admin-create-user \
  --user-pool-id $COGNITO_USER_POOL_ID \
  --username test@example.com \
  --temporary-password "TempPass123!" \
  --message-action SUPPRESS
```

#### Troubleshooting Deployment

**Common Issues:**

1. **Terraform Permission Errors:**
   ```bash
   # Ensure your AWS user has these policies:
   # - PowerUserAccess (recommended)
   # - Or custom policy with EC2, Lambda, API Gateway, Cognito, S3, DynamoDB, SQS, IAM permissions
   ```

2. **Lambda Deployment Failures:**
   ```bash
   # Check if infrastructure is deployed first
   terraform output
   
   # Verify Lambda package exists
   ls -la backend/deploy/lambda-deployment-package.zip
   
   # Check CloudWatch logs
   aws logs describe-log-groups --log-group-name-prefix /aws/lambda/receipt-search-dev
   ```

3. **Meilisearch Connection Issues:**
   ```bash
   # Check if EC2 instance is running
   aws ec2 describe-instances --filters "Name=tag:Name,Values=receipt-search-dev-meilisearch"
   
   # Check security group allows port 7700
   # Meilisearch runs in private subnet, accessible only from Lambda functions
   ```

#### First-Time Setup Checklist

- [ ] AWS CLI configured with appropriate permissions
- [ ] GitHub secrets configured
- [ ] Terraform infrastructure deployed successfully
- [ ] Lambda functions deployed and responding
- [ ] API Gateway endpoints returning expected responses
- [ ] Cognito user pool accessible
- [ ] Meilisearch instance running
- [ ] S3 bucket created and accessible
- [ ] DynamoDB tables created
- [ ] CloudWatch logs showing function executions

## 🔧 Configuration

### Environment Variables

```bash
# Required for deployment
export AWS_REGION=ap-southeast-1
export MEILISEARCH_MASTER_KEY=your_master_key_here

# Optional - set by Terraform
export COGNITO_USER_POOL_ID=ap-southeast-1_xxxxxxxxx
export COGNITO_CLIENT_ID=xxxxxxxxxxxxxxxxxxxxxxxxxx
export API_GATEWAY_URL=https://xxxxxxxxxx.execute-api.ap-southeast-1.amazonaws.com/dev
```

### GitHub Actions Configuration

The project includes a hybrid flexible CI/CD workflow that:
- ✅ Runs automatically on push/PR
- ✅ Supports manual triggers with options
- ✅ Includes comprehensive testing
- ✅ Optimizes for cost (smart deployment detection)

**Workflow features**:
- Code validation and linting
- Full test suite (unit, integration, e2e)
- Security scanning
- Infrastructure deployment (when enabled)
- Multi-environment support (dev/staging/prod)

## 📡 API Endpoints

After deployment, your API will be available at:
`https://[api-id].execute-api.ap-southeast-1.amazonaws.com/dev`

### Available Endpoints

- `GET /api/v1/health` - Health check
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/receipts` - Upload receipt
- `GET /api/v1/receipts` - List user receipts
- `GET /api/v1/receipts/{id}` - Get receipt details
- `DELETE /api/v1/receipts/{id}` - Delete receipt
- `GET /api/v1/search` - Search receipts

## 💰 Cost Management

### Stop Services (Save ~30-40% costs):
```bash
cd backend/deploy
./stop_services.sh
```

### Restart Services:
```bash
./start_services.sh
```

### What gets stopped:
- Meilisearch EC2 instance
- Non-essential resources
- Keeps Lambda functions (they're pay-per-use)

## 🧪 Testing

### Run Test Suite
```bash
# Unit tests
pytest backend/tests/unit/

# Integration tests  
pytest backend/tests/integration/

# End-to-end tests
pytest backend/tests/e2e/

# All tests
pytest
```

### Test Deployment
```bash
cd backend/deploy
./test_deployment.sh    # Test Lambda functions
./test_pipeline.sh      # Test end-to-end pipeline
./test_auth.sh         # Test authentication
```

## 🔍 Monitoring

- **API Gateway**: Logs and metrics in CloudWatch
- **Lambda Functions**: Individual function logs and metrics
- **Meilisearch**: EC2 instance monitoring
- **Queue Processing**: SQS metrics and dead letter queue monitoring

## 🛠️ Troubleshooting

### Common Issues

1. **503 Service Unavailable**: Expected for database-dependent endpoints when services are stopped
2. **Lambda timeout**: Check CloudWatch logs for specific function issues
3. **Authentication errors**: Verify Cognito configuration and tokens

### Useful Commands

```bash
# Check infrastructure status
cd infrastructure/terraform && terraform show

# View Lambda logs
aws logs tail /aws/lambda/receipt-search-dev-api --follow

# Check Meilisearch status (when running)
curl http://[private-ip]:7700/health
```

## 📝 Development

### Project Structure
```
receipt-search-app/
├── .github/workflows/          # GitHub Actions CI/CD
├── backend/
│   ├── src/                   # Python application code
│   ├── tests/                 # Test suite
│   └── deploy/               # Deployment scripts
├── infrastructure/
│   └── terraform/            # Infrastructure as code
└── README.md                 # This file
```

### Contributing

1. Create a feature branch
2. Make changes and add tests
3. Run test suite locally
4. Push to GitHub (triggers CI/CD)
5. Create pull request

## 📄 License

This project is private and proprietary.

---

**Last Updated**: September 12, 2025  
**Environment**: Development  
**Region**: ap-southeast-1 (Singapore)