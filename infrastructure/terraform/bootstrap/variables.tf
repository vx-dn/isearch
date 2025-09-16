# Variables for Bootstrap Configuration

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "aws_region" {
  description = "AWS region for backend resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project   = "receipt-search"
    Component = "terraform-backend"
    ManagedBy = "terraform"
  }
}