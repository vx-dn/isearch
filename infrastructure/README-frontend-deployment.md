# Frontend Deployment Guide

This guide covers deploying the Vue.js frontend to AWS using S3 + CloudFront.

## Architecture

```
Internet → CloudFront → S3 (Static Files)
                    ↓
               API Gateway → Lambda (Backend)
```

### AWS Resources Created

- **S3 Bucket**: Hosts the static frontend files
- **CloudFront Distribution**: CDN for fast global delivery
- **Origin Access Control**: Secure S3 access
- **Cache Behaviors**: Optimized caching for static assets and API calls

## Prerequisites

1. **Terraform Infrastructure**: Backend infrastructure must be deployed first
2. **AWS CLI**: Configured with appropriate permissions
3. **Node.js 18+**: For building the frontend
4. **Git**: For version tracking (optional)

## Deployment Methods

### 1. Automated Deployment (GitHub Actions)

The repository includes a GitHub Actions workflow that automatically deploys when changes are pushed to the `frontend/` directory.

**Setup:**
1. Configure repository secrets:
   ```
   AWS_ACCESS_KEY_ID=your_access_key
   AWS_SECRET_ACCESS_KEY=your_secret_key
   ```

2. Push changes to trigger deployment:
   ```bash
   git add frontend/
   git commit -m "Update frontend"
   git push origin main
   ```

### 2. Manual Deployment (Script)

Use the deployment script for one-off deployments:

```bash
# Deploy to dev (default)
./infrastructure/scripts/deploy-frontend.sh

# Deploy to production
./infrastructure/scripts/deploy-frontend.sh -e prod

# Deploy to staging in different region
./infrastructure/scripts/deploy-frontend.sh -e staging -r us-east-1
```

### 3. Manual Deployment (Step by Step)

#### Step 1: Deploy Infrastructure

First, ensure the CloudFront module is included in your Terraform:

```bash
cd infrastructure/terraform
terraform plan
terraform apply
```

#### Step 2: Get Infrastructure Outputs

```bash
# Get the S3 bucket name and CloudFront distribution ID
FRONTEND_BUCKET=$(terraform output -raw frontend_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)
API_URL=$(terraform output -raw api_url)
```

#### Step 3: Build the Frontend

```bash
cd ../../frontend

# Install dependencies
npm install

# Create production environment
cat > .env.production << EOF
VITE_API_URL=${API_URL}
VITE_APP_NAME="Receipt Search"
VITE_ENVIRONMENT=production
EOF

# Build the application
npm run build
```

#### Step 4: Deploy to S3

```bash
# Upload files with proper cache headers
aws s3 sync dist/ s3://${FRONTEND_BUCKET} \
  --delete \
  --cache-control "max-age=31536000" \
  --exclude "*.html"

# Upload HTML files with no-cache
aws s3 sync dist/ s3://${FRONTEND_BUCKET} \
  --cache-control "no-cache, no-store, must-revalidate" \
  --include "*.html"
```

#### Step 5: Invalidate CloudFront

```bash
aws cloudfront create-invalidation \
  --distribution-id ${CLOUDFRONT_ID} \
  --paths "/*"
```

## Environment Configuration

### Development
```env
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development
VITE_ENABLE_DEMO_MODE=true
```

### Production
```env
VITE_API_URL=https://your-api-domain.com
VITE_ENVIRONMENT=production
VITE_ENABLE_DEMO_MODE=false
VITE_ENABLE_ANALYTICS=true
```

## Custom Domain Setup

To use a custom domain (e.g., `app.yourdomain.com`):

### 1. Create SSL Certificate

```bash
# Create certificate in us-east-1 (required for CloudFront)
aws acm request-certificate \
  --domain-name app.yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

### 2. Update Terraform Variables

```hcl
# terraform.tfvars
frontend_custom_domain = "app.yourdomain.com"
frontend_acm_certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/abcd-1234"
```

### 3. Update DNS

Point your domain to the CloudFront distribution:

```
app.yourdomain.com CNAME d1234abcd.cloudfront.net
```

## Monitoring & Troubleshooting

### Check Deployment Status

```bash
# Check S3 bucket contents
aws s3 ls s3://${FRONTEND_BUCKET} --recursive

# Check CloudFront distribution
aws cloudfront get-distribution --id ${CLOUDFRONT_ID}

# Check invalidation status
aws cloudfront list-invalidations --distribution-id ${CLOUDFRONT_ID}
```

### Common Issues

1. **Build Failures**
   - Check Node.js version (requires 18+)
   - Verify all dependencies are installed
   - Check for TypeScript errors

2. **API Connection Issues**
   - Verify API_URL in environment variables
   - Check CORS configuration in backend
   - Confirm API Gateway is deployed

3. **Caching Issues**
   - Clear browser cache
   - Create CloudFront invalidation
   - Check cache-control headers

### Logs

- **Build logs**: Check GitHub Actions or local terminal
- **CloudFront logs**: Enable access logging if needed
- **Browser console**: Check for JavaScript errors

## Performance Optimization

### Cache Strategy

- **Static assets** (JS, CSS, images): 1 year cache (`max-age=31536000`)
- **HTML files**: No cache (`no-cache, no-store, must-revalidate`)
- **API calls**: No cache (proxied through CloudFront)

### Build Optimization

The frontend build includes:
- Code splitting
- Tree shaking
- Minification
- Gzip compression (via CloudFront)

## Security

- S3 bucket is private (no public access)
- CloudFront uses Origin Access Control
- HTTPS enforced (HTTP redirects to HTTPS)
- Security headers can be added via CloudFront Functions

## Cost Optimization

- CloudFront: ~$0.085/GB for first 10TB
- S3: ~$0.023/GB storage + $0.0004/1000 requests
- Typical monthly cost for small app: $5-20

## Rollback Process

To rollback a deployment:

1. **Identify previous version**:
   ```bash
   aws s3api list-object-versions --bucket ${FRONTEND_BUCKET}
   ```

2. **Restore from S3 versioning** or **redeploy previous commit**:
   ```bash
   git checkout previous-commit-hash
   ./infrastructure/scripts/deploy-frontend.sh
   ```

3. **Invalidate CloudFront cache**:
   ```bash
   aws cloudfront create-invalidation --distribution-id ${CLOUDFRONT_ID} --paths "/*"
   ```