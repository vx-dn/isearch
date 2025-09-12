# 🧹 AWS Infrastructure Cleanup Guide

## Quick Cleanup (Recommended)

To stop all services and delete all AWS resources:

```bash
cd /home/dev/psearch/receipt-search-app/backend/deploy
./cleanup.sh
```

This script will:
1. ✅ Delete all Lambda functions
2. ✅ Empty and delete S3 buckets  
3. ✅ Delete DynamoDB tables
4. ✅ Terminate EC2 instances (Meilisearch)
5. ✅ Remove VPC and networking
6. ✅ Delete Cognito user pools
7. ✅ Remove API Gateway
8. ✅ Delete SQS queues
9. ✅ Clean up local files

**Cost Impact**: All AWS charges will stop immediately.

## Verification

After cleanup, verify everything is deleted:

```bash
./verify_cleanup.sh
```

## Manual Cleanup Options

### Option 1: Terraform Destroy Only
If you just want to use Terraform to destroy infrastructure:

```bash
cd ../../infrastructure/terraform
terraform destroy -auto-approve
```

### Option 2: Selective Cleanup
If you want to keep some resources, you can manually delete:

#### Delete Lambda Functions
```bash
aws lambda delete-function --function-name receipt-search-dev-api --region ap-southeast-1
aws lambda delete-function --function-name receipt-search-dev-image-processor --region ap-southeast-1
aws lambda delete-function --function-name receipt-search-dev-text-extractor --region ap-southeast-1
aws lambda delete-function --function-name receipt-search-dev-cleanup-worker --region ap-southeast-1
```

#### Empty S3 Buckets
```bash
# Get bucket name
BUCKET_NAME=$(cd ../../infrastructure/terraform && terraform output -raw receipts_bucket_name)

# Empty bucket
aws s3 rm "s3://$BUCKET_NAME" --recursive --region ap-southeast-1
```

#### Stop EC2 Instance (Meilisearch)
```bash
# Get instance ID
INSTANCE_ID=$(cd ../../infrastructure/terraform && terraform output -raw meilisearch_instance_id)

# Stop instance
aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --region ap-southeast-1

# Or terminate completely
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region ap-southeast-1
```

## Immediate Cost Stoppers

If you need to stop costs immediately but plan to resume later:

### 1. Stop EC2 Instance (Biggest cost)
```bash
cd ../../infrastructure/terraform
INSTANCE_ID=$(terraform output -raw meilisearch_instance_id)
aws ec2 stop-instances --instance-ids "$INSTANCE_ID" --region ap-southeast-1
```

### 2. Delete Lambda Functions (No ongoing cost, but stops usage)
```bash
./cleanup.sh  # Answer 'no' when it asks to empty S3 buckets
```

## Recovery

If you need to redeploy later:

```bash
# Redeploy infrastructure
cd ../../infrastructure/terraform
terraform apply -auto-approve

# Redeploy Lambda functions  
cd ../../backend/deploy
./deploy_lambda.sh --all
```

## Cost Breakdown

When everything is deleted, you'll save:

| Service | Monthly Cost | Status After Cleanup |
|---------|-------------|---------------------|
| EC2 (t3.small) | ~$15-20 | ✅ Terminated |
| NAT Gateway | ~$32 | ✅ Deleted |
| S3 Storage | ~$1-5 | ✅ Deleted |
| DynamoDB | ~$0-5 | ✅ Deleted |
| Lambda | ~$0-1 | ✅ Deleted |
| API Gateway | ~$0-1 | ✅ Deleted |
| **Total Savings** | **~$50-65/month** | **✅ All costs stopped** |

## Troubleshooting

### If cleanup.sh fails:
1. Check AWS credentials: `aws sts get-caller-identity`
2. Manually empty S3 buckets first
3. Run terraform destroy manually
4. Check for remaining resources with `./verify_cleanup.sh`

### If resources remain:
- Some resources may have delete protection
- Check AWS Console for any remaining resources
- CloudWatch logs may take time to expire naturally

## ⚠️ Important Notes

- **Backup Data**: Make sure you have backups of any important data
- **Terraform State**: The cleanup script preserves terraform.tfstate for potential recovery
- **Immediate Effect**: Most resources are deleted immediately
- **Billing**: It may take up to 24 hours for all charges to stop appearing in AWS billing

---

**Ready to clean up? Run the cleanup script:**
```bash
./cleanup.sh
```
