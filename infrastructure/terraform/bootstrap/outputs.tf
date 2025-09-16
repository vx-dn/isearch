# Outputs for Bootstrap Configuration

output "state_bucket_name" {
  description = "Name of the created S3 bucket for Terraform state"
  value       = module.state_backend.state_bucket_name
}

output "lock_table_name" {
  description = "Name of the created DynamoDB table for state locking"
  value       = module.state_backend.lock_table_name
}

output "backend_config" {
  description = "Backend configuration for main Terraform setup"
  value       = module.state_backend.backend_config
}

output "backend_config_file" {
  description = "Path to the generated backend configuration file"
  value       = module.state_backend.backend_config_file
}

output "next_steps" {
  description = "Instructions for next steps"
  value = <<-EOT
    Backend resources created successfully!
    
    Next steps:
    1. Copy the generated backend configuration to your main terraform configuration
    2. Run: terraform init -backend-config=${module.state_backend.backend_config_file}
    3. Confirm the state migration when prompted
    
    Backend Configuration:
    bucket         = "${module.state_backend.backend_config.bucket}"
    key            = "${module.state_backend.backend_config.key}"
    region         = "${module.state_backend.backend_config.region}"
    dynamodb_table = "${module.state_backend.backend_config.dynamodb_table}"
    encrypt        = ${module.state_backend.backend_config.encrypt}
  EOT
}