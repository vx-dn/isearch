# Remote State Backend Configuration
#
# This file configures Terraform to use S3 for state storage with DynamoDB for state locking.
# The backend configuration is initialized dynamically based on the environment.
#
# Benefits:
# - Centralized state management across team members
# - State locking prevents concurrent modifications
# - State versioning and backup capabilities
# - Separation of state by environment

terraform {
  backend "s3" {
    # These values will be set dynamically during terraform init
    # using -backend-config parameters in the workflow
    
    # bucket         = "receipt-search-terraform-state-{environment}"
    # key            = "terraform.tfstate"
    # region         = "ap-southeast-1"
    # dynamodb_table = "receipt-search-terraform-locks-{environment}"
    # encrypt        = true
    
    # Enable state versioning for rollback capabilities
    # versioning = true
  }
}

# Data source to get current AWS account ID for bucket naming
data "aws_caller_identity" "current" {}

# Data source to get current AWS region
data "aws_region" "current" {}

# Locals for consistent naming
locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name
  
  # Construct backend resource names
  state_bucket_name = "receipt-search-terraform-state-${var.environment}-${local.account_id}"
  lock_table_name   = "receipt-search-terraform-locks-${var.environment}"
  
  # Common tags for backend resources
  backend_tags = merge(var.common_tags, {
    Purpose     = "terraform-state-backend"
    Environment = var.environment
    Component   = "infrastructure"
  })
}