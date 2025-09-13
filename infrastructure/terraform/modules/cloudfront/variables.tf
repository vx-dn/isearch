variable "name_prefix" {
  description = "Name prefix for resources"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "custom_domain" {
  description = "Custom domain name for the frontend (optional)"
  type        = string
  default     = null
}

variable "acm_certificate_arn" {
  description = "ARN of the ACM certificate for custom domain (optional)"
  type        = string
  default     = null
}

variable "api_gateway_domain_name" {
  description = "Domain name of the API Gateway for /api/* forwarding"
  type        = string
  default     = null
}