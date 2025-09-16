# IAM module for Lambda execution roles and policies

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

variable "account_id" {
  description = "AWS account ID"
  type        = string
}

variable "region" {
  description = "AWS region"
  type        = string
}

variable "receipts_bucket_arn" {
  description = "ARN of the receipts S3 bucket"
  type        = string
}

variable "receipts_table_arn" {
  description = "ARN of the receipts DynamoDB table"
  type        = string
}

variable "users_table_arn" {
  description = "ARN of the users DynamoDB table"
  type        = string
}

variable "processing_queue_arn" {
  description = "ARN of the processing SQS queue"
  type        = string
}

variable "dlq_arn" {
  description = "ARN of the dead letter queue"
  type        = string
}

# Basic Lambda execution role
resource "aws_iam_role" "lambda_execution" {
  name = "${var.name_prefix}-lambda-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Basic Lambda execution policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# VPC execution policy for Lambda
resource "aws_iam_role_policy_attachment" "lambda_vpc_execution" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.lambda_execution.name
}

# API Gateway Lambda role
resource "aws_iam_role" "api_lambda" {
  name = "${var.name_prefix}-api-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# API Lambda policies
resource "aws_iam_role_policy_attachment" "api_lambda_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.api_lambda.name
}

resource "aws_iam_role_policy_attachment" "api_lambda_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.api_lambda.name
}

# API Lambda custom policy
resource "aws_iam_role_policy" "api_lambda_policy" {
  name = "${var.name_prefix}-api-lambda-policy"
  role = aws_iam_role.api_lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:GetObjectVersion"
        ]
        Resource = [
          "${var.receipts_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = var.receipts_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          var.receipts_table_arn,
          "${var.receipts_table_arn}/index/*",
          var.users_table_arn,
          "${var.users_table_arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.processing_queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:AdminGetUser",
          "cognito-idp:AdminListGroupsForUser"
        ]
        Resource = "*"
      }
    ]
  })
}

# Image processor Lambda role
resource "aws_iam_role" "image_processor" {
  name = "${var.name_prefix}-image-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Image processor policies
resource "aws_iam_role_policy_attachment" "image_processor_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.image_processor.name
}

resource "aws_iam_role_policy_attachment" "image_processor_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.image_processor.name
}

resource "aws_iam_role_policy" "image_processor_policy" {
  name = "${var.name_prefix}-image-processor-policy"
  role = aws_iam_role.image_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${var.receipts_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = var.receipts_bucket_arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.processing_queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ]
        Resource = var.receipts_table_arn
      }
    ]
  })
}

# Text extractor Lambda role
resource "aws_iam_role" "text_extractor" {
  name = "${var.name_prefix}-text-extractor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Text extractor policies
resource "aws_iam_role_policy_attachment" "text_extractor_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.text_extractor.name
}

resource "aws_iam_role_policy_attachment" "text_extractor_vpc" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
  role       = aws_iam_role.text_extractor.name
}

resource "aws_iam_role_policy" "text_extractor_policy" {
  name = "${var.name_prefix}-text-extractor-policy"
  role = aws_iam_role.text_extractor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:GetObjectVersion"
        ]
        Resource = "${var.receipts_bucket_arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = [
          var.processing_queue_arn,
          var.dlq_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "textract:DetectDocumentText",
          "textract:AnalyzeDocument",
          "textract:StartDocumentTextDetection",
          "textract:GetDocumentTextDetection"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",
          "dynamodb:PutItem"
        ]
        Resource = [
          var.receipts_table_arn,
          var.users_table_arn
        ]
      }
    ]
  })
}

# Cleanup worker Lambda role
resource "aws_iam_role" "cleanup_worker" {
  name = "${var.name_prefix}-cleanup-worker-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Cleanup worker policies
resource "aws_iam_role_policy_attachment" "cleanup_worker_basic" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.cleanup_worker.name
}

resource "aws_iam_role_policy" "cleanup_worker_policy" {
  name = "${var.name_prefix}-cleanup-worker-policy"
  role = aws_iam_role.cleanup_worker.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.receipts_bucket_arn,
          "${var.receipts_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:DeleteItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = [
          var.receipts_table_arn,
          "${var.receipts_table_arn}/index/*",
          var.users_table_arn,
          "${var.users_table_arn}/index/*"
        ]
      }
    ]
  })
}

# EventBridge rule role for cleanup worker
resource "aws_iam_role" "eventbridge_cleanup" {
  name = "${var.name_prefix}-eventbridge-cleanup-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "events.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy" "eventbridge_cleanup_policy" {
  name = "${var.name_prefix}-eventbridge-cleanup-policy"
  role = aws_iam_role.eventbridge_cleanup.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = "arn:aws:lambda:${var.region}:${var.account_id}:function:${var.name_prefix}-cleanup-worker"
      }
    ]
  })
}

# Outputs
output "lambda_execution_role_arn" {
  description = "ARN of the basic Lambda execution role"
  value       = aws_iam_role.lambda_execution.arn
}

output "api_lambda_role_arn" {
  description = "ARN of the API Lambda role"
  value       = aws_iam_role.api_lambda.arn
}

output "image_processor_role_arn" {
  description = "ARN of the image processor Lambda role"
  value       = aws_iam_role.image_processor.arn
}

output "text_extractor_role_arn" {
  description = "ARN of the text extractor Lambda role"
  value       = aws_iam_role.text_extractor.arn
}

output "cleanup_worker_role_arn" {
  description = "ARN of the cleanup worker Lambda role"
  value       = aws_iam_role.cleanup_worker.arn
}

output "eventbridge_cleanup_role_arn" {
  description = "ARN of the EventBridge cleanup role"
  value       = aws_iam_role.eventbridge_cleanup.arn
}
