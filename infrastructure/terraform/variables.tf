# Global variables for the receipt search application infrastructure

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "receipt-search"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "free_user_image_quota" {
  description = "Maximum number of images for free users"
  type        = number
  default     = 50
}

variable "paid_user_image_quota" {
  description = "Maximum number of images for paid/admin users per month"
  type        = number
  default     = 1000
}

variable "free_user_retention_days" {
  description = "Number of days to retain free user data after inactivity"
  type        = number
  default     = 30
}

variable "meilisearch_master_key" {
  description = "Master key for Meilisearch authentication"
  type        = string
  sensitive   = true
}

variable "cognito_domain_prefix" {
  description = "Prefix for Cognito domain"
  type        = string
  default     = "receipt-search"
}

# Tags
variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "receipt-search"
    ManagedBy   = "terraform"
  }
}
