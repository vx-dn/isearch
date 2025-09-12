# DynamoDB module for receipt and user metadata storage

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

variable "free_user_image_quota" {
  description = "Maximum number of images for free users"
  type        = number
}

variable "paid_user_image_quota" {
  description = "Maximum number of images for paid/admin users"
  type        = number
}

variable "free_user_retention_days" {
  description = "Number of days to retain free user data"
  type        = number
}

# DynamoDB table for receipts
resource "aws_dynamodb_table" "receipts" {
  name           = "${var.name_prefix}-receipts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "receipt_id"

  attribute {
    name = "receipt_id"
    type = "S"
  }

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "upload_date"
    type = "S"
  }

  attribute {
    name = "processing_status"
    type = "S"
  }

  # GSI for querying receipts by user
  global_secondary_index {
    name            = "UserIndex"
    hash_key        = "user_id"
    range_key       = "upload_date"
    projection_type = "ALL"
  }

  # GSI for querying receipts by status (for processing)
  global_secondary_index {
    name            = "StatusIndex"
    hash_key        = "processing_status"
    range_key       = "upload_date"
    projection_type = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-receipts-table"
    Type = "receipts-metadata"
  })
}

# DynamoDB table for users
resource "aws_dynamodb_table" "users" {
  name           = "${var.name_prefix}-users"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "user_id"

  attribute {
    name = "user_id"
    type = "S"
  }

  attribute {
    name = "email"
    type = "S"
  }

  attribute {
    name = "last_active_date"
    type = "S"
  }

  # GSI for querying users by email
  global_secondary_index {
    name            = "EmailIndex"
    hash_key        = "email"
    projection_type = "ALL"
  }

  # GSI for querying inactive users (for cleanup)
  global_secondary_index {
    name            = "LastActiveIndex"
    hash_key        = "last_active_date"
    projection_type = "ALL"
  }

  # Point-in-time recovery
  point_in_time_recovery {
    enabled = true
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-users-table"
    Type = "user-metadata"
  })
}

# DynamoDB table for application configuration
resource "aws_dynamodb_table" "config" {
  name           = "${var.name_prefix}-config"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "config_key"

  attribute {
    name = "config_key"
    type = "S"
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-config-table"
    Type = "application-config"
  })
}

# Insert default configuration values
resource "aws_dynamodb_table_item" "free_user_quota" {
  table_name = aws_dynamodb_table.config.name
  hash_key   = aws_dynamodb_table.config.hash_key

  item = jsonencode({
    config_key = {
      S = "free_user_image_quota"
    }
    config_value = {
      N = tostring(var.free_user_image_quota)
    }
    description = {
      S = "Maximum number of images for free users"
    }
  })
}

resource "aws_dynamodb_table_item" "paid_user_quota" {
  table_name = aws_dynamodb_table.config.name
  hash_key   = aws_dynamodb_table.config.hash_key

  item = jsonencode({
    config_key = {
      S = "paid_user_image_quota"
    }
    config_value = {
      N = tostring(var.paid_user_image_quota)
    }
    description = {
      S = "Maximum number of images for paid/admin users per month"
    }
  })
}

resource "aws_dynamodb_table_item" "retention_days" {
  table_name = aws_dynamodb_table.config.name
  hash_key   = aws_dynamodb_table.config.hash_key

  item = jsonencode({
    config_key = {
      S = "free_user_retention_days"
    }
    config_value = {
      N = tostring(var.free_user_retention_days)
    }
    description = {
      S = "Number of days to retain free user data after inactivity"
    }
  })
}

# Outputs
output "receipts_table_name" {
  description = "Name of the receipts DynamoDB table"
  value       = aws_dynamodb_table.receipts.name
}

output "receipts_table_arn" {
  description = "ARN of the receipts DynamoDB table"
  value       = aws_dynamodb_table.receipts.arn
}

output "users_table_name" {
  description = "Name of the users DynamoDB table"
  value       = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  description = "ARN of the users DynamoDB table"
  value       = aws_dynamodb_table.users.arn
}

output "config_table_name" {
  description = "Name of the config DynamoDB table"
  value       = aws_dynamodb_table.config.name
}

output "config_table_arn" {
  description = "ARN of the config DynamoDB table"
  value       = aws_dynamodb_table.config.arn
}
