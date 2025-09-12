# Development environment configuration

# Environment-specific variables
environment = "dev"
aws_region  = "ap-southeast-1"

# User quotas
free_user_image_quota = 50
paid_user_image_quota = 1000
free_user_retention_days = 30

# Cognito domain (must be globally unique)
cognito_domain_prefix = "receipt-search-dev"

# Meilisearch master key (should be set via environment variable or tfvars file)
# meilisearch_master_key = "your-secure-master-key-here"

# Common tags
common_tags = {
  Project     = "receipt-search"
  Environment = "dev"
  ManagedBy   = "terraform"
  Owner       = "development-team"
}
