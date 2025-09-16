# Terraform State Backend Module
#
# This module creates the necessary AWS resources for Terraform remote state:
# - S3 bucket for state storage with versioning and encryption
# - DynamoDB table for state locking
# - Proper IAM policies for access control

# S3 Bucket for Terraform State
resource "aws_s3_bucket" "terraform_state" {
  bucket = var.state_bucket_name

  # Prevent accidental deletion of state bucket
  lifecycle {
    prevent_destroy = true
  }

  tags = merge(var.tags, {
    Name        = var.state_bucket_name
    Purpose     = "terraform-state-storage"
    Environment = var.environment
  })
}

# Enable versioning for state rollback capabilities
resource "aws_s3_bucket_versioning" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Enable server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# Block public access
resource "aws_s3_bucket_public_access_block" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle configuration for state management
resource "aws_s3_bucket_lifecycle_configuration" "terraform_state" {
  bucket = aws_s3_bucket.terraform_state.id

  rule {
    id     = "terraform_state_lifecycle"
    status = "Enabled"

    # Apply to all objects in the bucket
    filter {}

    # Keep non-current versions for 30 days
    noncurrent_version_expiration {
      noncurrent_days = 30
    }

    # Clean up incomplete multipart uploads
    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_locks" {
  name         = var.lock_table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }

  # Enable point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name        = var.lock_table_name
    Purpose     = "terraform-state-locking"
    Environment = var.environment
  })

  lifecycle {
    prevent_destroy = true
  }
}

# IAM policy for Terraform backend access
resource "aws_iam_policy" "terraform_backend" {
  name        = "terraform-backend-access-${var.environment}"
  description = "IAM policy for Terraform backend access in ${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketVersioning"
        ]
        Resource = aws_s3_bucket.terraform_state.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.terraform_state.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:DeleteItem"
        ]
        Resource = aws_dynamodb_table.terraform_locks.arn
      }
    ]
  })

  tags = var.tags
}

# Output the backend configuration
resource "local_file" "backend_config" {
  content = templatefile("${path.module}/backend-config.tpl", {
    bucket         = aws_s3_bucket.terraform_state.bucket
    key            = "terraform.tfstate"
    region         = data.aws_region.current.name
    dynamodb_table = aws_dynamodb_table.terraform_locks.name
    encrypt        = "true"
  })
  filename = "${path.root}/backend-config-${var.environment}.hcl"
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}