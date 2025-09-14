# AWS OIDC Setup for GitHub Actions

This guide helps you set up OpenID Connect (OIDC) role assumption for secure AWS deployments from GitHub Actions without storing long-term access keys.

## Benefits of OIDC

✅ **Enhanced Security** - No long-term credentials stored in GitHub secrets  
✅ **Automatic Rotation** - Temporary credentials that expire quickly  
✅ **Fine-grained Control** - Restrict access to specific repositories and branches  
✅ **Audit Trail** - Better CloudTrail logging with role assumption  

## Setup Steps

### 1. Create OIDC Identity Provider in AWS

Run this AWS CLI command or use the AWS Console:

```bash
aws iam create-open-id-connect-identity-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. Create IAM Roles for Each Environment

#### Development Role

```json
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

#### Production Role (More Restrictive)

```json
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
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:vx-dn/isearch:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

### 3. Attach Policies to Roles

Attach these AWS managed policies to each role:

**For Infrastructure Deployment:**
- `PowerUserAccess` (or create custom policy with specific permissions)

**For Lambda Deployment:**
- Custom policy with Lambda, S3, and CloudWatch permissions

**For Frontend Deployment:**
- Custom policy with S3 and CloudFront permissions

### 4. Create AWS CLI Script

Create `setup-oidc-roles.sh`:

```bash
#!/bin/bash

# Variables
ACCOUNT_ID="YOUR_ACCOUNT_ID"
REPO="vx-dn/isearch"
REGION="ap-southeast-1"

# Create OIDC Provider (run once per account)
aws iam create-open-id-connect-identity-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create trust policy template
cat > trust-policy-template.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRole",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:${REPO}:BRANCH_CONDITION"
        }
      }
    }
  ]
}
EOF

# Create roles for each environment
for ENV in dev staging prod; do
    if [ "$ENV" = "prod" ]; then
        BRANCH_CONDITION="ref:refs/heads/main"
    else
        BRANCH_CONDITION="*"
    fi
    
    # Create trust policy for this environment
    sed "s/BRANCH_CONDITION/$BRANCH_CONDITION/" trust-policy-template.json > trust-policy-${ENV}.json
    
    # Create the role
    aws iam create-role \
        --role-name GitHubActions-ReceiptSearch-${ENV} \
        --assume-role-policy-document file://trust-policy-${ENV}.json \
        --description "Role for GitHub Actions deployment to ${ENV} environment"
    
    # Attach policies (customize based on your needs)
    aws iam attach-role-policy \
        --role-name GitHubActions-ReceiptSearch-${ENV} \
        --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
    
    echo "Created role: GitHubActions-ReceiptSearch-${ENV}"
    echo "Role ARN: arn:aws:iam::${ACCOUNT_ID}:role/GitHubActions-ReceiptSearch-${ENV}"
done

# Clean up temporary files
rm trust-policy-*.json

echo "Setup complete! Add these role ARNs to your GitHub secrets:"
echo "AWS_ROLE_ARN_DEV: arn:aws:iam::${ACCOUNT_ID}:role/GitHubActions-ReceiptSearch-dev"
echo "AWS_ROLE_ARN_STAGING: arn:aws:iam::${ACCOUNT_ID}:role/GitHubActions-ReceiptSearch-staging"
echo "AWS_ROLE_ARN_PROD: arn:aws:iam::${ACCOUNT_ID}:role/GitHubActions-ReceiptSearch-prod"
```

### 5. Required GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

```
AWS_ROLE_ARN_DEV=arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-ReceiptSearch-dev
AWS_ROLE_ARN_STAGING=arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-ReceiptSearch-staging  
AWS_ROLE_ARN_PROD=arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-ReceiptSearch-prod
AWS_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT_ID:role/GitHubActions-ReceiptSearch-prod

# Keep these for services that need them
MEILISEARCH_MASTER_KEY_DEV=your-dev-meilisearch-key
MEILISEARCH_MASTER_KEY_STAGING=your-staging-meilisearch-key  
MEILISEARCH_MASTER_KEY_PROD=your-prod-meilisearch-key
MEILISEARCH_MASTER_KEY=your-prod-meilisearch-key
```

### 6. Test the Setup

1. **Commit and push** your workflow changes
2. **Go to Actions tab** in GitHub
3. **Run a workflow manually** to test OIDC authentication
4. **Check CloudTrail** to verify role assumption is working

## Security Best Practices

1. **Principle of Least Privilege** - Only grant necessary permissions
2. **Environment-Specific Roles** - Separate roles for dev/staging/prod
3. **Branch Restrictions** - Restrict production role to main branch only
4. **Regular Auditing** - Review CloudTrail logs for unauthorized access
5. **Policy Validation** - Use AWS IAM Policy Simulator to test permissions

## Troubleshooting

### Common Issues:

1. **"No OpenIDConnect provider found"**
   - Ensure OIDC provider is created in the correct AWS account

2. **"Not authorized to perform sts:AssumeRole"**
   - Check trust policy conditions (repository, branch)
   - Verify GitHub repository settings

3. **"Token audience invalid"**
   - Ensure `aud` condition is set to `sts.amazonaws.com`

### Debug Steps:

1. Check IAM role trust relationships
2. Verify repository name format: `repo:owner/repository:condition`
3. Ensure workflow has proper permissions block
4. Test with AWS STS get-caller-identity

## Migration from Access Keys

1. **Set up OIDC roles** (this guide)
2. **Test workflows** with OIDC
3. **Remove old secrets** (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
4. **Delete IAM users** that were used for GitHub Actions

This setup significantly improves security by eliminating long-term credentials while maintaining the same deployment functionality.