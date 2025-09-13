# Receipt Search App

A full-stack serverless receipt search application with Vue.js frontend and Python FastAPI backend, built for intelligent document processing and search.

## 🏗️ Architecture

- **Frontend**: Vue.js 3 + TypeScript with S3/CloudFront hosting
- **Backend**: Python FastAPI with AWS Lambda
- **Search**: Meilisearch for full-text search
- **Authentication**: AWS Cognito
- **Storage**: S3 for files, DynamoDB for metadata
- **Processing**: AWS Textract for OCR
- **Infrastructure**: Terraform for AWS resources
- **CI/CD**: GitHub Actions for automated deployment

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
   cd isearch/receipt-search-app
   ```

2. **Backend setup**:
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env with your actual values (never commit this file!)
   
   # Install dependencies
   pip install -r requirements-dev.txt
   
   # Run tests
   pytest
   ```

3. **Frontend setup**:
   ```bash
   cd ../frontend
   npm install
   
   # Create environment file
   cp .env.example .env.local
   # Edit with your backend URL
   
   # Start development server
   npm run dev
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
- **`backend/deploy/requirements-lambda.txt`** - Lambda-optimized production deployment

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

### Frontend Deployment

The frontend is a Vue.js application that provides a ChatGPT-like interface for receipt search functionality.

#### Option 1: GitHub Actions (Recommended)

**Prerequisites:**
Ensure backend infrastructure is deployed first (see backend deployment above).

**Step 1: Deploy Infrastructure with Frontend**
```bash
cd infrastructure/terraform

# Deploy both backend and frontend infrastructure
terraform apply -var-file=environments/dev.tfvars

# Note the frontend URL from outputs
terraform output frontend_url
```

**Step 2: Automated Frontend Deployment**
```bash
# Frontend automatically deploys when you push changes to main branch
git add frontend/
git commit -m "Deploy frontend updates"
git push origin main

# Or trigger manual deployment in GitHub Actions:
# 1. Go to Actions tab in GitHub
# 2. Select "Deploy Frontend" workflow  
# 3. Click "Run workflow"
```

#### Option 2: Manual Frontend Deployment

**Prerequisites:**
```bash
# Ensure Node.js 18+ is installed
node --version

# Ensure AWS CLI is configured
aws --version
```

**Step 1: Build Frontend**
```bash
cd frontend

# Install dependencies
npm install

# Build for production
npm run build
```

**Step 2: Deploy to AWS**
```bash
# Make deployment script executable
chmod +x ../infrastructure/scripts/deploy-frontend.sh

# Deploy frontend to S3/CloudFront
../infrastructure/scripts/deploy-frontend.sh
```

**Step 3: Verify Deployment**
```bash
# Get frontend URL from Terraform
cd ../infrastructure/terraform
terraform output frontend_url

# Test health endpoint
curl https://your-frontend-url.com/health.json

# Visit the URL in browser
```

#### Frontend Architecture

```
Users → CloudFront CDN → S3 Static Files
      → CloudFront CDN → API Gateway → Lambda Functions (for /api/* requests)
```

**Components:**
- **S3 Bucket**: Hosts static files (HTML, CSS, JS)
- **CloudFront**: Global CDN for fast content delivery
- **API Proxy**: Routes `/api/*` requests to backend API Gateway
- **Health Check**: `/health.json` endpoint for monitoring

#### Frontend Configuration

**Environment Variables:**
```bash
# Frontend environment variables (.env.production)
VITE_API_BASE_URL=https://your-api-gateway-url.com/dev
VITE_APP_TITLE="Receipt Search"
VITE_ENABLE_ANALYTICS=true
```

**Build Configuration:**
- **Framework**: Vue.js 3 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Pinia
- **Routing**: Vue Router

#### Frontend Features

- ✅ **Chat Interface**: ChatGPT-like conversation UI
- ✅ **Receipt Upload**: Drag & drop file upload
- ✅ **Smart Search**: Natural language search queries
- ✅ **Authentication**: Integrated with AWS Cognito
- ✅ **Responsive**: Mobile-friendly design
- ✅ **Real-time**: Live search and updates
- ✅ **Error Handling**: User-friendly error messages

#### Troubleshooting Deployment

**Common Backend Issues:**

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

**Common Frontend Issues:**

1. **Build Failures:**
   ```bash
   # Check Node.js version (requires 18+)
   node --version
   
   # Clear npm cache and reinstall
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   
   # Check for TypeScript errors
   npm run type-check
   ```

2. **API Connection Issues:**
   ```bash
   # Verify backend is deployed and accessible
   curl https://your-api-gateway-url.com/dev/api/v1/health
   
   # Check CORS configuration in API Gateway
   # Ensure frontend domain is allowed in CORS origins
   
   # Verify environment variables
   cat frontend/.env.production
   ```

3. **CloudFront/S3 Issues:**
   ```bash
   # Check S3 bucket exists and has files
   aws s3 ls s3://your-frontend-bucket-name --recursive
   
   # Verify CloudFront distribution status
   aws cloudfront list-distributions --query 'DistributionList.Items[].{Id:Id,Status:Status,DomainName:DomainName}'
   
   # Create cache invalidation if needed
   aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
   ```

4. **Deployment Script Issues:**
   ```bash
   # Make script executable
   chmod +x infrastructure/scripts/deploy-frontend.sh
   
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Run script with debug
   bash -x infrastructure/scripts/deploy-frontend.sh
   ```

#### First-Time Setup Checklist

**Backend Setup:**
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

**Frontend Setup:**
- [ ] Node.js 18+ installed
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Frontend builds successfully (`npm run build`)
- [ ] S3 bucket for frontend hosting created
- [ ] CloudFront distribution deployed and active
- [ ] Frontend accessible via CloudFront URL
- [ ] API calls working from frontend to backend
- [ ] Health check endpoint responding
- [ ] Authentication flow working end-to-end

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

## 📡 API Endpoints & Frontend

### Frontend Application
After deployment, your frontend will be available at:
`https://[cloudfront-id].cloudfront.net` or your custom domain

**Frontend Features:**
- Chat-based interface for receipt interaction
- Upload receipts via drag & drop
- Search receipts using natural language
- View receipt details and extracted data
- User authentication and profile management

### Backend API
API endpoints are available at:
`https://[api-id].execute-api.ap-southeast-1.amazonaws.com/dev`

**Available Endpoints:**
- `GET /api/v1/health` - Health check
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/auth/me` - Get current user
- `POST /api/v1/receipts` - Upload receipt
- `GET /api/v1/receipts` - List user receipts
- `GET /api/v1/receipts/{id}` - Get receipt details
- `DELETE /api/v1/receipts/{id}` - Delete receipt
- `GET /api/v1/search` - Search receipts

## 💰 Cost Management

### Monthly Cost Estimates

**Backend Services:**
- Lambda functions: ~$5-15 (usage-based)
- API Gateway: ~$3-10 (per million requests)
- EC2 (Meilisearch): ~$15-30 (t3.small instance)
- S3 storage: ~$1-5 (depending on receipts stored)
- DynamoDB: ~$1-5 (usage-based)

**Frontend Services:**
- S3 hosting: ~$0.02 (1GB storage)
- CloudFront CDN: ~$0.85 (10GB data transfer)
- Route 53 (if using custom domain): ~$0.50

**Total estimated cost: $25-65/month** (varies by usage)

### Stop Services (Save ~60% costs):
```bash
cd backend/deploy
./stop_services.sh
```

### Restart Services:
```bash
./start_services.sh
```

**What gets stopped:**
- Meilisearch EC2 instance (biggest cost saver)
- Non-essential resources
- Keeps Lambda functions (pay-per-use)
- Keeps S3 and CloudFront (minimal cost when not accessed)

## 🧪 Testing

### Backend Testing
```bash
cd backend

# Unit tests
pytest tests/unit/

# Integration tests  
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/

# All tests
pytest
```

### Frontend Testing
```bash
cd frontend

# Unit tests
npm run test:unit

# End-to-end tests
npm run test:e2e

# Type checking
npm run type-check

# Linting
npm run lint
```

### Test Deployment
```bash
cd backend/deploy
./test_deployment.sh    # Test Lambda functions
./test_pipeline.sh      # Test end-to-end pipeline
./test_auth.sh         # Test authentication

# Test frontend health
curl https://your-frontend-url.com/health.json
```

## 🔍 Monitoring

### Backend Monitoring
- **API Gateway**: Logs and metrics in CloudWatch
- **Lambda Functions**: Individual function logs and metrics
- **Meilisearch**: EC2 instance monitoring
- **Queue Processing**: SQS metrics and dead letter queue monitoring

### Frontend Monitoring
- **CloudFront**: Distribution metrics and cache performance
- **S3**: Storage metrics and request patterns  
- **Health Check**: Monitor `/health.json` endpoint
- **User Analytics**: Optional integration with analytics services

### Useful Monitoring Commands
```bash
# Backend health
curl https://your-api-gateway-url.com/dev/api/v1/health

# Frontend health  
curl https://your-frontend-url.com/health.json

# Check CloudFront distribution status
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID

# View recent CloudFront logs
aws logs tail /aws/cloudfront/YOUR_DISTRIBUTION_ID --follow
```

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
│   ├── hybrid-deploy.yml      # Backend deployment workflow
│   └── deploy-frontend.yml    # Frontend deployment workflow
├── backend/
│   ├── src/                   # Python application code
│   ├── tests/                 # Test suite
│   └── deploy/               # Deployment scripts
├── frontend/
│   ├── src/                   # Vue.js application code
│   ├── public/               # Static assets
│   ├── dist/                 # Built files (generated)
│   └── package.json          # Node.js dependencies
├── infrastructure/
│   ├── terraform/            # Infrastructure as code
│   │   └── modules/          # Terraform modules
│   │       └── cloudfront/   # Frontend hosting module
│   └── scripts/              # Deployment scripts
│       └── deploy-frontend.sh
└── README.md                 # This file
```

### Contributing

1. Create a feature branch
2. Make changes and add tests (backend: pytest, frontend: npm test)
3. Run test suite locally
4. Push to GitHub (triggers CI/CD)
5. Create pull request

## � Documentation

- **Backend API**: See `backend/README.md` for detailed API documentation
- **Frontend**: See `frontend/README.md` for component documentation  
- **Infrastructure**: See `infrastructure/README.md` for Terraform details
- **Deployment**: See `FRONTEND-DEPLOYMENT-SUMMARY.md` for frontend deployment details

## �📄 License

This project is private and proprietary.

---

**Last Updated**: September 13, 2025  
**Environment**: Development  
**Region**: ap-southeast-1 (Singapore)  
**Architecture**: Full-stack serverless with Vue.js frontend and Python FastAPI backend