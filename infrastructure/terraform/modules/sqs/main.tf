# SQS module for asynchronous processing

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

# Dead Letter Queue for failed processing
resource "aws_sqs_queue" "dead_letter" {
  name                       = "${var.name_prefix}-processing-dlq"
  message_retention_seconds  = 1209600 # 14 days
  
  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-processing-dlq"
    Type = "dead-letter-queue"
  })
}

# Main processing queue
resource "aws_sqs_queue" "processing" {
  name                       = "${var.name_prefix}-processing-queue"
  delay_seconds              = 0
  max_message_size          = 262144 # 256 KB
  message_retention_seconds  = 1209600 # 14 days
  receive_wait_time_seconds  = 20 # Long polling
  visibility_timeout_seconds = 300 # 5 minutes

  # Dead letter queue configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dead_letter.arn
    maxReceiveCount     = 3
  })

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-processing-queue"
    Type = "processing-queue"
  })
}

# SQS queue policy to allow S3 and Lambda access
resource "aws_sqs_queue_policy" "processing" {
  queue_url = aws_sqs_queue.processing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "s3.amazonaws.com"
        }
        Action   = "sqs:SendMessage"
        Resource = aws_sqs_queue.processing.arn
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      },
      {
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = aws_sqs_queue.processing.arn
      }
    ]
  })
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.name_prefix}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateNumberOfMessages"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Average"
  threshold           = "0"
  alarm_description   = "This metric monitors dlq message count"
  alarm_actions       = [] # Add SNS topic ARN here for notifications

  dimensions = {
    QueueName = aws_sqs_queue.dead_letter.name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "queue_age" {
  alarm_name          = "${var.name_prefix}-queue-message-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "600" # 10 minutes
  alarm_description   = "This metric monitors message age in processing queue"
  alarm_actions       = [] # Add SNS topic ARN here for notifications

  dimensions = {
    QueueName = aws_sqs_queue.processing.name
  }

  tags = var.common_tags
}

# Outputs
output "processing_queue_url" {
  description = "URL of the processing SQS queue"
  value       = aws_sqs_queue.processing.url
}

output "processing_queue_arn" {
  description = "ARN of the processing SQS queue"
  value       = aws_sqs_queue.processing.arn
}

output "processing_queue_name" {
  description = "Name of the processing SQS queue"
  value       = aws_sqs_queue.processing.name
}

output "dead_letter_queue_url" {
  description = "URL of the dead letter SQS queue"
  value       = aws_sqs_queue.dead_letter.url
}

output "dead_letter_queue_arn" {
  description = "ARN of the dead letter SQS queue"
  value       = aws_sqs_queue.dead_letter.arn
}

output "dead_letter_queue_name" {
  description = "Name of the dead letter SQS queue"
  value       = aws_sqs_queue.dead_letter.name
}
