# EC2 module for Meilisearch deployment
# Updated to use Amazon Linux 2023 kernel-6.12 AMI and Session Manager access

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

variable "vpc_id" {
  description = "ID of the VPC"
  type        = string
}

variable "private_subnet_id" {
  description = "ID of the private subnet"
  type        = string
}

variable "meilisearch_master_key" {
  description = "Master key for Meilisearch"
  type        = string
  sensitive   = true
}

variable "lambda_security_group_id" {
  description = "ID of the Lambda security group"
  type        = string
}

# Data sources
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-kernel-6.12-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

data "aws_region" "current" {}

# Key pair for EC2 access
resource "aws_key_pair" "meilisearch" {
  key_name   = "${var.name_prefix}-meilisearch-key"
  public_key = tls_private_key.meilisearch.public_key_openssh

  tags = var.common_tags
}

resource "tls_private_key" "meilisearch" {
  algorithm = "RSA"
  rsa_bits  = 4096
}

# Store private key in AWS Secrets Manager
resource "aws_secretsmanager_secret" "meilisearch_private_key" {
  name        = "${var.name_prefix}/meilisearch/private-key"
  description = "Private key for Meilisearch EC2 instance"

  tags = var.common_tags
}

resource "aws_secretsmanager_secret_version" "meilisearch_private_key" {
  secret_id     = aws_secretsmanager_secret.meilisearch_private_key.id
  secret_string = tls_private_key.meilisearch.private_key_pem
}

# Security group for Meilisearch
resource "aws_security_group" "meilisearch" {
  name_prefix = "${var.name_prefix}-meilisearch-sg"
  vpc_id      = var.vpc_id

  # Meilisearch API port from Lambda
  ingress {
    from_port       = 7700
    to_port         = 7700
    protocol        = "tcp"
    security_groups = [var.lambda_security_group_id]
    description     = "Meilisearch API from Lambda"
  }

  # SSH access from VPC
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/16"]
    description = "SSH from VPC"
  }

  # All outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic (includes Session Manager endpoints)"
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-meilisearch-sg"
  })
}

# IAM role for EC2 instance
resource "aws_iam_role" "meilisearch_ec2" {
  name = "${var.name_prefix}-meilisearch-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# IAM policy for EC2 instance
resource "aws_iam_role_policy" "meilisearch_ec2" {
  name = "${var.name_prefix}-meilisearch-ec2-policy"
  role = aws_iam_role.meilisearch_ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.name_prefix}-meilisearch-backups-*",
          "arn:aws:s3:::${var.name_prefix}-meilisearch-backups-*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:PutLogEvents",
          "logs:CreateLogGroup",
          "logs:CreateLogStream"
        ]
        Resource = "*"
      }
    ]
  })
}

# Attach AWS managed policy for Session Manager
resource "aws_iam_role_policy_attachment" "ssm_managed_instance_core" {
  role       = aws_iam_role.meilisearch_ec2.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Instance profile
resource "aws_iam_instance_profile" "meilisearch" {
  name = "${var.name_prefix}-meilisearch-profile"
  role = aws_iam_role.meilisearch_ec2.name

  tags = var.common_tags
}

# S3 bucket for Meilisearch backups
resource "aws_s3_bucket" "meilisearch_backups" {
  bucket = "${var.name_prefix}-meilisearch-backups-${random_id.backup_bucket_suffix.hex}"

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-meilisearch-backups"
    Type = "meilisearch-backups"
  })
}

resource "random_id" "backup_bucket_suffix" {
  byte_length = 4
}

# S3 bucket encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "meilisearch_backups" {
  bucket = aws_s3_bucket.meilisearch_backups.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 bucket lifecycle for backups
resource "aws_s3_bucket_lifecycle_configuration" "meilisearch_backups" {
  bucket = aws_s3_bucket.meilisearch_backups.id

  rule {
    id     = "backup_retention"
    status = "Enabled"

    filter {
      prefix = ""
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}

# User data script for EC2 instance
locals {
  user_data = templatefile("${path.module}/user_data.sh", {
    meilisearch_master_key = var.meilisearch_master_key
    backup_bucket         = aws_s3_bucket.meilisearch_backups.bucket
    region               = data.aws_region.current.id
  })
}

# EC2 instance for Meilisearch
resource "aws_instance" "meilisearch" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = "t3.micro"
  key_name              = aws_key_pair.meilisearch.key_name
  vpc_security_group_ids = [aws_security_group.meilisearch.id]
  subnet_id             = var.private_subnet_id
  iam_instance_profile  = aws_iam_instance_profile.meilisearch.name

  user_data                   = local.user_data
  user_data_replace_on_change = true

  # EBS configuration
  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  # Instance metadata options
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-meilisearch"
    Type = "meilisearch-server"
  })
}

# CloudWatch alarm for instance health
resource "aws_cloudwatch_metric_alarm" "meilisearch_status_check" {
  alarm_name          = "${var.name_prefix}-meilisearch-status-check"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "StatusCheckFailed"
  namespace           = "AWS/EC2"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "0"
  alarm_description   = "This metric monitors meilisearch instance status check"

  dimensions = {
    InstanceId = aws_instance.meilisearch.id
  }

  tags = var.common_tags
}

# Outputs
output "instance_id" {
  description = "ID of the Meilisearch EC2 instance"
  value       = aws_instance.meilisearch.id
}

output "private_ip" {
  description = "Private IP of the Meilisearch EC2 instance"
  value       = aws_instance.meilisearch.private_ip
}

output "security_group_id" {
  description = "ID of the Meilisearch security group"
  value       = aws_security_group.meilisearch.id
}

output "backup_bucket_name" {
  description = "Name of the Meilisearch backup S3 bucket"
  value       = aws_s3_bucket.meilisearch_backups.bucket
}

output "private_key_secret_arn" {
  description = "ARN of the secret containing the private key"
  value       = aws_secretsmanager_secret.meilisearch_private_key.arn
}
