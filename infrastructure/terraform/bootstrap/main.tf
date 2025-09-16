# Bootstrap Configuration for Terraform State Backend
#
# This configuration creates the S3 bucket and DynamoDB table required
# for Terraform remote state before the main infrastructure deployment.
#
# Usage:
# 1. Run this first to create backend resources
# 2. Copy the generated backend config to main Terraform configuration
# 3. Run terraform init with -backend-config to migrate to remote state

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.0"
    }
  }
}

# Provider configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = var.common_tags
  }
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Locals for consistent naming
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  
  # Construct backend resource names
  state_bucket_name = "receipt-search-terraform-state-${var.environment}-${local.account_id}"
  lock_table_name   = "receipt-search-terraform-locks-${var.environment}"
}

# Create the state backend using our module
module "state_backend" {
  source = "../modules/state-backend"
  
  environment       = var.environment
  state_bucket_name = local.state_bucket_name
  lock_table_name   = local.lock_table_name
  region            = local.region
  tags              = var.common_tags
}