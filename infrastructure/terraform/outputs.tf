# Output values for the receipt search application infrastructure

# S3 outputs
output "receipts_bucket_name" {
  description = "Name of the S3 bucket for receipt storage"
  value       = module.s3.receipts_bucket_name
}

output "receipts_bucket_arn" {
  description = "ARN of the S3 bucket for receipt storage"
  value       = module.s3.receipts_bucket_arn
}

# DynamoDB outputs
output "receipts_table_name" {
  description = "Name of the DynamoDB table for receipts"
  value       = module.dynamodb.receipts_table_name
}

output "users_table_name" {
  description = "Name of the DynamoDB table for users"
  value       = module.dynamodb.users_table_name
}

# SQS outputs
output "processing_queue_url" {
  description = "URL of the SQS queue for processing"
  value       = module.sqs.processing_queue_url
}

output "processing_queue_arn" {
  description = "ARN of the SQS queue for processing"
  value       = module.sqs.processing_queue_arn
}

# Cognito outputs
output "cognito_user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = module.cognito.user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = module.cognito.user_pool_client_id
}

output "cognito_domain" {
  description = "Cognito domain for authentication"
  value       = module.cognito.cognito_domain
}

# Frontend outputs
output "frontend_url" {
  description = "URL of the frontend application"
  value       = module.cloudfront.frontend_url
}

output "frontend_bucket_name" {
  description = "Name of the S3 bucket for frontend hosting"
  value       = module.cloudfront.frontend_bucket_name
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution for frontend"
  value       = module.cloudfront.cloudfront_distribution_id
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = module.cloudfront.cloudfront_domain_name
}

# API Gateway outputs
output "api_url" {
  description = "URL of the API Gateway"
  value       = module.api_gateway.api_url
}

output "api_id" {
  description = "ID of the API Gateway"
  value       = module.api_gateway.api_id
}

# IAM outputs
output "lambda_execution_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.iam.lambda_execution_role_arn
}

output "image_processor_role_arn" {
  description = "ARN of the image processor Lambda role"
  value       = module.iam.image_processor_role_arn
}

output "text_extractor_role_arn" {
  description = "ARN of the text extractor Lambda role"
  value       = module.iam.text_extractor_role_arn
}

# VPC outputs
output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "lambda_security_group_id" {
  description = "ID of the Lambda security group"
  value       = module.vpc.lambda_security_group_id
}

# EC2 outputs
output "meilisearch_instance_id" {
  description = "ID of the Meilisearch EC2 instance"
  value       = module.ec2.instance_id
}

output "meilisearch_private_ip" {
  description = "Private IP of the Meilisearch EC2 instance"
  value       = module.ec2.private_ip
}

output "meilisearch_security_group_id" {
  description = "ID of the Meilisearch security group"
  value       = module.ec2.security_group_id
}

# API Gateway outputs
output "api_gateway_url" {
  description = "URL of the API Gateway"
  value       = module.api_gateway.api_url
}

output "api_gateway_id" {
  description = "ID of the API Gateway"
  value       = module.api_gateway.api_id
}
