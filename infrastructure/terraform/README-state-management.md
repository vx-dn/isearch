# Terraform Remote State Management

This document describes the remote state management setup for the Receipt Search application infrastructure.

## Overview

The infrastructure uses Terraform remote state with the following components:

- **S3 Bucket**: Stores the Terraform state files with encryption and versioning
- **DynamoDB Table**: Provides state locking to prevent concurrent modifications
- **Environment Separation**: Each environment (dev/staging/prod) has its own backend resources

## Benefits

✅ **Team Collaboration**: Multiple team members can work with the same state  
✅ **State Locking**: Prevents conflicts from concurrent Terraform runs  
✅ **State Versioning**: Ability to rollback to previous state versions  
✅ **Security**: State is encrypted at rest and in transit  
✅ **Backup & Recovery**: Automatic state backup and point-in-time recovery  

## Backend Architecture

```
Environment: dev
├── S3 Bucket: receipt-search-terraform-state-dev-{account-id}
│   ├── terraform.tfstate (current state)
│   ├── Previous versions (30-day retention)
│   └── Encryption: AES-256
└── DynamoDB Table: receipt-search-terraform-locks-dev
    ├── Hash Key: LockID
    ├── Point-in-time Recovery: Enabled
    └── Encryption: Enabled
```

## Setup Process

### 1. Initialize Backend Resources

Run this workflow **once per environment** to create the S3 bucket and DynamoDB table:

```bash
# Via GitHub Actions
Go to Actions → "Initialize Terraform Backend"
Select environment: dev/staging/prod
Select action: create
```

This creates:
- S3 bucket for state storage
- DynamoDB table for state locking
- IAM policies for backend access

### 2. Migrate Existing State (If Applicable)

If you have existing local state files, use the migration workflow:

```bash
# Via GitHub Actions
Go to Actions → "Migrate Terraform State" 
Select environment: dev/staging/prod
Type "MIGRATE" to confirm
Enable backup: true (recommended)
```

⚠️ **IMPORTANT**: This is a one-way migration. Ensure you have backups.

### 3. Deploy Infrastructure

Use the standard infrastructure deployment workflow:

```bash
# Via GitHub Actions
Go to Actions → "Infrastructure Deployment"
Select environment: dev/staging/prod
Select action: plan/apply
```

The workflow automatically configures remote state backend.

## File Structure

```
infrastructure/terraform/
├── backend.tf                 # Backend configuration template
├── bootstrap/                 # Backend initialization
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── dev.tfvars
│   ├── staging.tfvars
│   └── prod.tfvars
├── modules/state-backend/      # Backend resources module
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   └── backend-config.tpl
└── environments/              # Environment configs
    ├── dev.tfvars
    ├── staging.tfvars
    └── prod.tfvars
```

## State Backend Configuration

The backend is configured dynamically per environment:

```hcl
# Example for dev environment
terraform {
  backend "s3" {
    bucket         = "receipt-search-terraform-state-dev-123456789012"
    key            = "terraform.tfstate"
    region         = "ap-southeast-1"
    dynamodb_table = "receipt-search-terraform-locks-dev"
    encrypt        = true
  }
}
```

## Workflows

### terraform-backend-init.yml
- **Purpose**: Create backend resources (S3 + DynamoDB)
- **When to use**: Once per environment, before any infrastructure deployment
- **Actions**: create, destroy, status

### terraform-state-migration.yml  
- **Purpose**: Migrate local state to remote backend
- **When to use**: When you have existing local state files
- **Safety**: Requires explicit "MIGRATE" confirmation

### infrastructure-deploy.yml
- **Purpose**: Deploy main infrastructure
- **Updated**: Now uses remote state automatically
- **Features**: State locking, team collaboration ready

## Manual Commands

If you need to work with Terraform locally:

```bash
# Initialize with remote backend
terraform init \
  -backend-config="bucket=receipt-search-terraform-state-dev-123456789012" \
  -backend-config="key=terraform.tfstate" \
  -backend-config="region=ap-southeast-1" \
  -backend-config="dynamodb_table=receipt-search-terraform-locks-dev" \
  -backend-config="encrypt=true"

# Plan with environment-specific variables
terraform plan -var-file="environments/dev.tfvars"

# Apply changes
terraform apply -var-file="environments/dev.tfvars"
```

## Security Considerations

🔒 **State Encryption**: All state files are encrypted at rest (AES-256)  
🔒 **Access Control**: IAM policies restrict backend access  
🔒 **Network Security**: S3 bucket blocks all public access  
🔒 **State Locking**: DynamoDB prevents concurrent modifications  
🔒 **Audit Trail**: CloudTrail logs all state access  

## Cost Considerations

The backend resources have minimal AWS costs:

- **S3 Storage**: ~$0.023/GB/month for state files (typically <1MB)
- **S3 Requests**: ~$0.0004 per 1,000 requests
- **DynamoDB**: Pay-per-request pricing (typically <$1/month)
- **Total**: Usually <$5/month per environment

## Troubleshooting

### State Lock Issues

If state is locked and won't unlock:

```bash
# Force unlock (use with caution)
terraform force-unlock <LOCK_ID>
```

### Backend Access Issues

Verify IAM permissions for:
- S3: `s3:ListBucket`, `s3:GetObject`, `s3:PutObject`
- DynamoDB: `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:DeleteItem`

### Migration Issues

If migration fails:
1. Ensure backend resources exist
2. Verify local state file is present
3. Check AWS credentials and permissions
4. Review backup files if restoration is needed

## Best Practices

✅ **One backend per environment**: Separate dev/staging/prod state  
✅ **Regular state backups**: S3 versioning provides automatic backups  
✅ **Team coordination**: Use shared remote state, avoid local state  
✅ **State locking**: Always use DynamoDB for locking  
✅ **Access control**: Limit backend access to necessary team members  
✅ **Monitor costs**: Review S3 and DynamoDB usage regularly  

## Recovery Procedures

### Restore Previous State Version

```bash
# List state versions
aws s3api list-object-versions \
  --bucket receipt-search-terraform-state-dev-123456789012 \
  --prefix terraform.tfstate

# Download specific version
aws s3api get-object \
  --bucket receipt-search-terraform-state-dev-123456789012 \
  --key terraform.tfstate \
  --version-id <VERSION_ID> \
  terraform.tfstate.backup
```

### Emergency Local State Recovery

If remote state is corrupted:

1. Download latest working state version from S3
2. Copy to local `terraform.tfstate` file  
3. Run `terraform init -reconfigure -backend=false`
4. Fix issues and re-migrate to remote backend

## Support

For issues with remote state management:

1. Check GitHub Actions workflow logs
2. Verify AWS permissions and resources
3. Review Terraform state list: `terraform state list`
4. Contact the infrastructure team for assistance