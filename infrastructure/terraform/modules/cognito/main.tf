# Cognito module for user authentication

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

variable "domain_prefix" {
  description = "Prefix for Cognito domain"
  type        = string
}

# Cognito User Pool
resource "aws_cognito_user_pool" "main" {
  name = "${var.name_prefix}-user-pool"

  # Password policy
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = true
    require_uppercase = true
  }

  # Username configuration - allow email as username
  username_attributes = ["email"]

  # Auto-verified attributes
  auto_verified_attributes = ["email"]

  # Account recovery
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Email configuration
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # User attributes
  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "email"
    required                 = true

    string_attribute_constraints {
      min_length = 1
      max_length = 256
    }
  }

  schema {
    attribute_data_type      = "String"
    developer_only_attribute = false
    mutable                  = true
    name                     = "role"
    required                 = false

    string_attribute_constraints {
      min_length = 1
      max_length = 20
    }
  }

  # MFA configuration
  mfa_configuration = "OFF"

  # Device configuration
  device_configuration {
    challenge_required_on_new_device      = false
    device_only_remembered_on_user_prompt = false
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-user-pool"
    Type = "authentication"
  })
}

# Cognito User Pool Client
resource "aws_cognito_user_pool_client" "main" {
  name         = "${var.name_prefix}-app-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Token validity
  access_token_validity  = 60 # 60 minutes
  id_token_validity      = 60 # 60 minutes
  refresh_token_validity = 30 # 30 days

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  # Explicit auth flows
  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH"
  ]

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # OAuth configuration
  supported_identity_providers = ["COGNITO"]

  allowed_oauth_flows  = ["code"]
  allowed_oauth_scopes = ["email", "openid", "profile"]

  callback_urls = [
    "http://localhost:3000/callback",           # Development
    "https://your-frontend-domain.com/callback" # Production - update this
  ]

  logout_urls = [
    "http://localhost:3000/logout",
    "https://your-frontend-domain.com/logout"
  ]

  # Security
  generate_secret = false

  # Read and write attributes
  read_attributes  = ["email", "custom:role"]
  write_attributes = ["email"]
}

# Cognito User Pool Domain
resource "aws_cognito_user_pool_domain" "main" {
  domain       = var.domain_prefix
  user_pool_id = aws_cognito_user_pool.main.id
}

# Cognito Identity Pool for AWS resource access
resource "aws_cognito_identity_pool" "main" {
  identity_pool_name               = "${var.name_prefix}-identity-pool"
  allow_unauthenticated_identities = false

  cognito_identity_providers {
    client_id               = aws_cognito_user_pool_client.main.id
    provider_name           = aws_cognito_user_pool.main.endpoint
    server_side_token_check = false
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-identity-pool"
    Type = "identity"
  })
}

# IAM roles for authenticated users
resource "aws_cognito_identity_pool_roles_attachment" "main" {
  identity_pool_id = aws_cognito_identity_pool.main.id

  roles = {
    "authenticated" = aws_iam_role.authenticated.arn
  }
}

# IAM role for authenticated users
resource "aws_iam_role" "authenticated" {
  name = "${var.name_prefix}-cognito-authenticated-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = "cognito-identity.amazonaws.com"
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "cognito-identity.amazonaws.com:aud" = aws_cognito_identity_pool.main.id
          }
          "ForAnyValue:StringLike" = {
            "cognito-identity.amazonaws.com:amr" = "authenticated"
          }
        }
      }
    ]
  })

  tags = var.common_tags
}

# Basic policy for authenticated users
resource "aws_iam_role_policy" "authenticated" {
  name = "${var.name_prefix}-cognito-authenticated-policy"
  role = aws_iam_role.authenticated.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-sync:*",
          "cognito-identity:*"
        ]
        Resource = "*"
      }
    ]
  })
}

# Create default admin user (optional - remove in production)
# resource "aws_cognito_user" "admin" {
#   user_pool_id = aws_cognito_user_pool.main.id
#   username     = "admin@example.com"
#   
#   attributes = {
#     email          = "admin@example.com"
#     email_verified = "true"
#     "custom:role"  = "admin"
#   }
#   
#   temporary_password = "TempPassword123!"
#   message_action     = "SUPPRESS"
# }

# Outputs
output "user_pool_id" {
  description = "ID of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.arn
}

output "user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool"
  value       = aws_cognito_user_pool.main.endpoint
}

output "user_pool_client_id" {
  description = "ID of the Cognito User Pool Client"
  value       = aws_cognito_user_pool_client.main.id
}

output "cognito_domain" {
  description = "Cognito domain for authentication"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "identity_pool_id" {
  description = "ID of the Cognito Identity Pool"
  value       = aws_cognito_identity_pool.main.id
}
