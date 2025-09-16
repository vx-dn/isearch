# Staging environment configuration

# Environment-specific variables
environment = "staging"
aws_region  = "ap-southeast-1"

# User quotas
free_user_image_quota    = 50
paid_user_image_quota    = 1000
free_user_retention_days = 30

# Cognito domain (must be globally unique)
cognito_domain_prefix = "receipt-search-staging"

# NOTE: Sensitive values like meilisearch_master_key are provided via GitHub secrets
# and passed as environment variables to Terraform (TF_VAR_meilisearch_master_key)

# Common tags
common_tags = {
  Project     = "receipt-search"
  Environment = "staging"
  ManagedBy   = "terraform"
  Owner       = "development-team"
}