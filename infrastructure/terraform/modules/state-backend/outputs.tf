# Outputs for Terraform State Backend Module

output "state_bucket_name" {
  description = "Name of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.bucket
}

output "state_bucket_arn" {
  description = "ARN of the S3 bucket for Terraform state"
  value       = aws_s3_bucket.terraform_state.arn
}

output "lock_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "lock_table_arn" {
  description = "ARN of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.arn
}

output "backend_policy_arn" {
  description = "ARN of the IAM policy for backend access"
  value       = aws_iam_policy.terraform_backend.arn
}

output "backend_config_file" {
  description = "Path to the generated backend configuration file"
  value       = local_file.backend_config.filename
}

output "backend_config" {
  description = "Backend configuration values"
  value = {
    bucket         = aws_s3_bucket.terraform_state.bucket
    key            = "terraform.tfstate"
    region         = data.aws_region.current.name
    dynamodb_table = aws_dynamodb_table.terraform_locks.name
    encrypt        = true
  }
}