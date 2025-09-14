# Main Terraform configuration for receipt search application

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.12.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.common_tags, {
      Environment = var.environment
    })
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Local values
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  account_id  = data.aws_caller_identity.current.account_id
  region      = data.aws_region.current.id
}

# S3 module for receipt storage
module "s3" {
  source = "./modules/s3"

  name_prefix = local.name_prefix
  environment = var.environment
  common_tags = var.common_tags
  region      = var.aws_region
  account_id  = data.aws_caller_identity.current.account_id
}

# DynamoDB module for metadata storage
module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix              = local.name_prefix
  environment              = var.environment
  common_tags              = var.common_tags
  free_user_image_quota    = var.free_user_image_quota
  paid_user_image_quota    = var.paid_user_image_quota
  free_user_retention_days = var.free_user_retention_days
}

# SQS module for async processing
module "sqs" {
  source = "./modules/sqs"

  name_prefix = local.name_prefix
  environment = var.environment
  common_tags = var.common_tags
}

# Cognito module for authentication
module "cognito" {
  source = "./modules/cognito"

  name_prefix   = local.name_prefix
  environment   = var.environment
  common_tags   = var.common_tags
  domain_prefix = "${var.cognito_domain_prefix}-${var.environment}"
}

# IAM module for roles and policies
module "iam" {
  source = "./modules/iam"

  name_prefix          = local.name_prefix
  environment          = var.environment
  common_tags          = var.common_tags
  account_id           = local.account_id
  region               = local.region
  receipts_bucket_arn  = module.s3.receipts_bucket_arn
  receipts_table_arn   = module.dynamodb.receipts_table_arn
  users_table_arn      = module.dynamodb.users_table_arn
  processing_queue_arn = module.sqs.processing_queue_arn
  dlq_arn              = module.sqs.dead_letter_queue_arn
}

# VPC module for EC2 and Lambda networking
module "vpc" {
  source = "./modules/vpc"

  name_prefix = local.name_prefix
  environment = var.environment
  common_tags = var.common_tags
}

# EC2 module for Meilisearch
module "ec2" {
  source = "./modules/ec2"

  name_prefix              = local.name_prefix
  environment              = var.environment
  common_tags              = var.common_tags
  vpc_id                   = module.vpc.vpc_id
  private_subnet_id        = module.vpc.private_subnet_id
  meilisearch_master_key   = var.meilisearch_master_key
  lambda_security_group_id = module.vpc.lambda_security_group_id
}

# API Gateway module
module "api_gateway" {
  source = "./modules/api_gateway"

  name_prefix = local.name_prefix
  environment = var.environment
  common_tags = var.common_tags
}

# CloudFront module for frontend hosting
module "cloudfront" {
  source = "./modules/cloudfront"

  name_prefix             = local.name_prefix
  environment             = var.environment
  common_tags             = var.common_tags
  api_gateway_domain_name = module.api_gateway.api_gateway_domain_name
  custom_domain           = var.frontend_custom_domain
  acm_certificate_arn     = var.frontend_acm_certificate_arn
}
