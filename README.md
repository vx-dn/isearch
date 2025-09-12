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

2. **Install dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Run tests**:
   ```bash
   pytest
   ```

### Deployment

#### Option 1: GitHub Actions (Recommended)

1. **Configure secrets** in GitHub repository settings → Secrets and variables → Actions:
   - `AWS_ACCESS_KEY_ID`
   - `AWS_SECRET_ACCESS_KEY`
   - `MEILISEARCH_MASTER_KEY`

2. **Manual trigger**:
   - Go to Actions tab in GitHub
   - Select "🔧 Hybrid Flexible CI/CD" workflow
   - Click "Run workflow"
   - Choose environment: `dev`
   - Enable "Deploy infrastructure" if needed

3. **Automatic trigger**: Push to `main` or `develop` branch

#### Option 2: Manual Deployment

1. **Deploy infrastructure**:
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan -var-file=environments/dev.tfvars
   terraform apply -var-file=environments/dev.tfvars
   ```

2. **Deploy Lambda functions**:
   ```bash
   cd backend/deploy
   ./deploy_lambda.sh
   ```

3. **Test deployment**:
   ```bash
   ./test_deployment.sh
   ```

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