# 🚀 GitHub Actions Workflows Documentation

This document describes the GitHub Actions workflows for the receipt search application.

## 📋 Available Workflows

### 🏗️ **Infrastructure Deployment** (`infrastructure-deploy.yml`)
Deploy Terraform infrastructure to AWS across multiple environments.

**Triggers:**
- **Automatic**: Push to `main` with infrastructure changes
- **Manual**: `workflow_dispatch` with environment selection

**Features:**
- ✅ Environment-specific deployments (dev/staging/prod)
- ✅ Terraform plan/apply/destroy operations
- ✅ OIDC authentication with AWS
- ✅ Environment variable validation
- ✅ Sensitive values via GitHub secrets

**Required Secrets:**
- `AWS_ROLE_ARN_DEV/STAGING/PROD` - IAM role ARNs for OIDC
- `MEILISEARCH_MASTER_KEY_DEV/STAGING/PROD` - Meilisearch authentication

### 🐍 **Backend Deployment** (`backend-deploy.yml`)
Deploy the FastAPI backend application to AWS Lambda.

**Triggers:**
- **Automatic**: Push to `main` with backend changes
- **Manual**: `workflow_dispatch` with environment selection

**Features:**
- ✅ Python testing and linting
- ✅ Lambda function deployment
- ✅ Environment-specific configurations
- ✅ Health check validation

### 🌐 **Frontend Deployment** (`frontend-deploy.yml`)
Deploy the React frontend application to AWS S3 and CloudFront.

**Triggers:**
- **Automatic**: Push to `main` with frontend changes
- **Manual**: `workflow_dispatch` with environment selection

**Features:**
- ✅ TypeScript compilation and testing
- ✅ S3 static website deployment
- ✅ CloudFront distribution invalidation
- ✅ Environment-specific configurations

### 🔍 **OIDC Connection Test** (`test-oidc.yml`)
Debug and validate OIDC connection to AWS for troubleshooting.

**Triggers:**
- **Manual only**: `workflow_dispatch` with environment selection

**Features:**
- ✅ OIDC connection validation
- ✅ Secret availability checking
- ✅ Detailed error messages and setup instructions
- ✅ AWS role assumption testing

## 🎯 **Deployment Strategy**

### Development Workflow
1. **Feature Development**: Work on feature branches
2. **Pull Request**: Create PR to `main` for review
3. **Manual Testing**: Use `workflow_dispatch` to deploy to dev environment
4. **Merge to Main**: Automatic deployment to staging

### Production Deployment
1. **Validation**: Ensure staging deployment is successful
2. **Manual Trigger**: Use `workflow_dispatch` to deploy to production
3. **Environment Protection**: Production requires manual approval (configure in repo settings)

## 🔒 **Security Setup**

### AWS OIDC Configuration
1. **Create OIDC Provider** in AWS IAM
2. **Create IAM Roles** for each environment with appropriate trust policies
3. **Add GitHub Secrets** with role ARNs

### Required GitHub Secrets
```
# AWS Authentication
AWS_ROLE_ARN_DEV=arn:aws:iam::123456789012:role/GitHubActions-Infrastructure-dev
AWS_ROLE_ARN_STAGING=arn:aws:iam::123456789012:role/GitHubActions-Infrastructure-staging  
AWS_ROLE_ARN_PROD=arn:aws:iam::123456789012:role/GitHubActions-Infrastructure-prod

# Application Secrets
MEILISEARCH_MASTER_KEY_DEV=your-dev-key-here
MEILISEARCH_MASTER_KEY_STAGING=your-staging-key-here
MEILISEARCH_MASTER_KEY_PROD=your-prod-key-here
```

## 🛠️ **Manual Deployment Examples**

### Deploy Infrastructure to Development
```bash
# GitHub UI: Actions → Infrastructure Deployment → Run workflow
Environment: dev
Terraform action: apply
Auto-approve: false
```

### Deploy Backend to Production
```bash
# GitHub UI: Actions → Backend Deployment → Run workflow
Environment: prod
```

### Test OIDC Connection
```bash
# GitHub UI: Actions → Test OIDC Connection → Run workflow
Environment: prod
```

## 📊 **Best Practices**

### Branch Protection
- ✅ Require PR reviews for `main` branch
- ✅ Require status checks to pass
- ✅ Restrict pushes to `main`

### Environment Protection
- ✅ Configure environment protection rules for production
- ✅ Require manual approval for production deployments
- ✅ Restrict deployment to specific branches

### Secret Management
- ✅ Use environment-specific secrets
- ✅ Rotate secrets regularly
- ✅ Use least-privilege IAM policies
- ✅ Never commit secrets to version control

## 🔧 **Troubleshooting**

### Common Issues

#### OIDC Authentication Errors
1. **"No OpenIDConnect provider found"**
   - Ensure OIDC provider is created in the correct AWS account
   - Verify provider URL: `https://token.actions.githubusercontent.com`

2. **"Not authorized to perform sts:AssumeRole"**
   - Check IAM role trust policy conditions (repository, branch)
   - Verify GitHub repository settings match trust policy
   - Ensure workflow has proper permissions block

3. **"Token audience invalid"**
   - Ensure `aud` condition is set to `sts.amazonaws.com` in trust policy

4. **"Access Denied" when assuming role**
   - Check IAM role permissions policy
   - Verify role ARN format in GitHub secrets

#### Terraform Issues
1. **"Variables file not found"**
   - Verify tfvars files exist for target environment
   - Check file naming: `environments/{environment}.tfvars`

2. **"Required variable not set"**
   - Ensure sensitive variables are provided via GitHub secrets
   - Check secret naming format: `MEILISEARCH_MASTER_KEY_{ENV}`

#### Deployment Failures
1. **Lambda deployment timeout**
   - Check function size and dependencies
   - Verify Lambda configuration limits

2. **S3 deployment access denied**
   - Verify IAM role has S3 permissions
   - Check bucket policies and ACLs

### Debug Steps
1. **Use test-oidc.yml workflow** to validate AWS authentication
2. **Check workflow logs** for detailed error messages
3. **Verify IAM role trust relationships** in AWS console
4. **Test repository name format**: `repo:owner/repository:*`
5. **Validate GitHub secrets** are properly configured

### OIDC Setup Commands
If you need to set up OIDC from scratch:

```bash
# Create OIDC Identity Provider
aws iam create-open-id-connect-identity-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Example IAM role trust policy
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:vx-dn/isearch:*"
        }
      }
    }
  ]
}
```

## 📚 **Additional Resources**

- [AWS OIDC Setup Guide](./AWS_OIDC_SETUP.md) - Detailed AWS configuration
- [GitHub Secrets Setup](../docs/github-secrets-setup.md) - Secret configuration guide
- [Terraform Documentation](../infrastructure/terraform/README.md) - Infrastructure details