# API Gateway module for REST API

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

# API Gateway REST API
resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.name_prefix}-api"
  description = "Receipt Search Application API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  # CORS configuration
  body = jsonencode({
    openapi = "3.0.1"
    info = {
      title   = "Receipt Search API"
      version = "1.0"
    }
    paths = {
      "/{proxy+}" = {
        x-amazon-apigateway-any-method = {
          x-amazon-apigateway-integration = {
            type                = "AWS_PROXY"
            httpMethod          = "POST"
            uri                 = "arn:aws:apigateway:${data.aws_region.current.id}:lambda:path/2015-03-31/functions/arn:aws:lambda:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:function:${var.name_prefix}-api-handler/invocations"
            passthroughBehavior = "WHEN_NO_MATCH"
          }
        }
        options = {
          responses = {
            "200" = {
              description = "200 response"
              headers = {
                "Access-Control-Allow-Origin" = {
                  schema = {
                    type = "string"
                  }
                }
                "Access-Control-Allow-Headers" = {
                  schema = {
                    type = "string"
                  }
                }
                "Access-Control-Allow-Methods" = {
                  schema = {
                    type = "string"
                  }
                }
              }
            }
          }
          x-amazon-apigateway-integration = {
            type = "MOCK"
            requestTemplates = {
              "application/json" = "{\"statusCode\": 200}"
            }
            responses = {
              default = {
                statusCode = "200"
                responseParameters = {
                  "method.response.header.Access-Control-Allow-Origin"  = "'*'"
                  "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
                  "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS,POST,PUT,DELETE'"
                }
              }
            }
          }
        }
      }
    }
  })

  tags = merge(var.common_tags, {
    Name = "${var.name_prefix}-api-gateway"
  })
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# API Gateway deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_rest_api.main.body,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [aws_api_gateway_rest_api.main]
}

# API Gateway stage
resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.environment

  # CloudWatch logging
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_gateway.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      user           = "$context.identity.user"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
      errorMessage   = "$context.error.message"
      errorType      = "$context.error.messageString"
    })
  }

  tags = var.common_tags

  depends_on = [aws_api_gateway_account.main]
}

# CloudWatch log group for API Gateway
resource "aws_cloudwatch_log_group" "api_gateway" {
  name              = "/aws/apigateway/${var.name_prefix}-api"
  retention_in_days = 14

  tags = var.common_tags
}

# IAM role for API Gateway CloudWatch logging
resource "aws_iam_role" "cloudwatch_role" {
  name = "${var.name_prefix}-api-gateway-cloudwatch-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

# Attach the managed policy for API Gateway to push logs to CloudWatch
resource "aws_iam_role_policy_attachment" "cloudwatch_role_policy" {
  role       = aws_iam_role.cloudwatch_role.id
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}

# API Gateway account settings
resource "aws_api_gateway_account" "main" {
  cloudwatch_role_arn = aws_iam_role.cloudwatch_role.arn
}

# API Gateway method settings
resource "aws_api_gateway_method_settings" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = aws_api_gateway_stage.main.stage_name
  method_path = "*/*"

  settings {
    metrics_enabled        = true
    logging_level          = "INFO"
    data_trace_enabled     = false
    throttling_rate_limit  = 100
    throttling_burst_limit = 200
  }
}

# API Gateway usage plan
resource "aws_api_gateway_usage_plan" "main" {
  name        = "${var.name_prefix}-usage-plan"
  description = "Usage plan for Receipt Search API"

  api_stages {
    api_id = aws_api_gateway_rest_api.main.id
    stage  = aws_api_gateway_stage.main.stage_name
  }

  quota_settings {
    limit  = 10000
    period = "DAY"
  }

  throttle_settings {
    rate_limit  = 100
    burst_limit = 200
  }

  tags = var.common_tags
}

# API Gateway API key
resource "aws_api_gateway_api_key" "main" {
  name        = "${var.name_prefix}-api-key"
  description = "API key for Receipt Search application"
  enabled     = true

  tags = var.common_tags
}

# Associate API key with usage plan
resource "aws_api_gateway_usage_plan_key" "main" {
  key_id        = aws_api_gateway_api_key.main.id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.main.id
}

# Lambda permission for API Gateway (will be enabled when Lambda functions are created)
# resource "aws_lambda_permission" "api_gateway" {
#   statement_id  = "AllowExecutionFromAPIGateway"
#   action        = "lambda:InvokeFunction" 
#   function_name = "${var.name_prefix}-api-handler"
#   principal     = "apigateway.amazonaws.com"
#   source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
# }# CloudWatch alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "api_4xx_errors" {
  alarm_name          = "${var.name_prefix}-api-4xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "4XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "10"
  alarm_description   = "This metric monitors api gateway 4xx errors"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.id
    Stage   = aws_api_gateway_stage.main.stage_name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_5xx_errors" {
  alarm_name          = "${var.name_prefix}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors api gateway 5xx errors"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.id
    Stage   = aws_api_gateway_stage.main.stage_name
  }

  tags = var.common_tags
}

resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "${var.name_prefix}-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = "300"
  statistic           = "Average"
  threshold           = "5000" # 5 seconds
  alarm_description   = "This metric monitors api gateway latency"

  dimensions = {
    ApiName = aws_api_gateway_rest_api.main.id
    Stage   = aws_api_gateway_stage.main.stage_name
  }

  tags = var.common_tags
}

# Outputs
output "api_id" {
  description = "ID of the API Gateway"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_arn" {
  description = "ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.main.arn
}

output "api_url" {
  description = "URL of the API Gateway"
  value       = "https://${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.id}.amazonaws.com/${var.environment}"
}

output "api_execution_arn" {
  description = "Execution ARN of the API Gateway"
  value       = aws_api_gateway_rest_api.main.execution_arn
}

output "api_key_id" {
  description = "ID of the API key"
  value       = aws_api_gateway_api_key.main.id
}

output "api_key_value" {
  description = "Value of the API key"
  value       = aws_api_gateway_api_key.main.value
  sensitive   = true
}

output "api_gateway_domain_name" {
  description = "Domain name of the API Gateway"
  value       = "${aws_api_gateway_rest_api.main.id}.execute-api.${data.aws_region.current.id}.amazonaws.com"
}
