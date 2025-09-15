# S3 module for receipt storage

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to resources"
  type        = map(string)
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

# S3 bucket for receipt storage
resource "aws_s3_bucket" "receipts" {
  bucket = "${var.name_prefix}-receipts-${random_id.bucket_suffix.hex}"

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-receipts-bucket"
    Type = "receipts-storage"
  })
}

# Random suffix for bucket name uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 bucket versioning
resource "aws_s3_bucket_versioning" "receipts" {
  bucket = aws_s3_bucket.receipts.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}

# S3 bucket public access block
resource "aws_s3_bucket_public_access_block" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 bucket lifecycle configuration
resource "aws_s3_bucket_lifecycle_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  rule {
    id     = "temp_uploads_cleanup"
    status = "Enabled"

    filter {
      prefix = "temp/"
    }

    expiration {
      days = 1
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }
  }

  rule {
    id     = "free_user_cleanup"
    status = "Enabled"

    filter {
      prefix = "free-users/"
    }

    # Free user files will be managed by application logic
    # This rule is for extra safety cleanup after 45 days
    expiration {
      days = 45
    }
  }

  rule {
    id     = "multipart_upload_cleanup"
    status = "Enabled"

    filter {
      prefix = ""
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }
}

# Note: Lambda permissions and S3 notifications are handled in the backend deployment
# The Lambda function is deployed separately via the backend-deploy workflow

# CORS configuration for presigned URL uploads
resource "aws_s3_bucket_cors_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = ["*"] # Should be restricted to frontend domain in production
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Outputs
output "receipts_bucket_name" {
  description = "Name of the receipts S3 bucket"
  value       = aws_s3_bucket.receipts.id
}

output "receipts_bucket_arn" {
  description = "ARN of the receipts S3 bucket"
  value       = aws_s3_bucket.receipts.arn
}

output "receipts_bucket_domain_name" {
  description = "Domain name of the receipts S3 bucket"
  value       = aws_s3_bucket.receipts.bucket_domain_name
}
