#!/bin/bash

# Quick cleanup verification script
# Run this after cleanup.sh to verify all resources are gone

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[CHECK]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[FOUND]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[VERIFY]${NC} $1"
}

AWS_REGION=${AWS_REGION:-ap-southeast-1}

print_header "Verifying AWS Resource Cleanup"
echo "==============================="
echo ""

# Check Lambda functions
print_status "Checking Lambda functions..."
LAMBDAS=$(aws lambda list-functions --region "$AWS_REGION" --query 'Functions[?starts_with(FunctionName, `receipt-search`)].FunctionName' --output table 2>/dev/null || echo "None")
if [[ "$LAMBDAS" == "None" || -z "$LAMBDAS" ]]; then
    print_status "✅ No Lambda functions found"
else
    print_error "❌ Found Lambda functions:"
    echo "$LAMBDAS"
fi

# Check S3 buckets
print_status "Checking S3 buckets..."
BUCKETS=$(aws s3api list-buckets --region "$AWS_REGION" --query 'Buckets[?starts_with(Name, `receipt-search`)].Name' --output table 2>/dev/null || echo "None")
if [[ "$BUCKETS" == "None" || -z "$BUCKETS" ]]; then
    print_status "✅ No S3 buckets found"
else
    print_error "❌ Found S3 buckets:"
    echo "$BUCKETS"
fi

# Check DynamoDB tables
print_status "Checking DynamoDB tables..."
TABLES=$(aws dynamodb list-tables --region "$AWS_REGION" --query 'TableNames[?starts_with(@, `receipt-search`)]' --output table 2>/dev/null || echo "None")
if [[ "$TABLES" == "None" || -z "$TABLES" ]]; then
    print_status "✅ No DynamoDB tables found"
else
    print_error "❌ Found DynamoDB tables:"
    echo "$TABLES"
fi

# Check EC2 instances
print_status "Checking EC2 instances..."
INSTANCES=$(aws ec2 describe-instances --region "$AWS_REGION" --filters "Name=tag:Project,Values=receipt-search" "Name=instance-state-name,Values=running,pending,stopping,stopped" --query 'Reservations[].Instances[].{InstanceId:InstanceId,State:State.Name,Name:Tags[?Key==`Name`].Value|[0]}' --output table 2>/dev/null || echo "None")
if [[ "$INSTANCES" == "None" || -z "$INSTANCES" ]]; then
    print_status "✅ No EC2 instances found"
else
    print_error "❌ Found EC2 instances:"
    echo "$INSTANCES"
fi

# Check API Gateway
print_status "Checking API Gateway..."
APIS=$(aws apigateway get-rest-apis --region "$AWS_REGION" --query 'items[?starts_with(name, `receipt-search`)].{Name:name,Id:id}' --output table 2>/dev/null || echo "None")
if [[ "$APIS" == "None" || -z "$APIS" ]]; then
    print_status "✅ No API Gateway APIs found"
else
    print_error "❌ Found API Gateway APIs:"
    echo "$APIS"
fi

# Check Cognito User Pools
print_status "Checking Cognito User Pools..."
USER_POOLS=$(aws cognito-idp list-user-pools --max-results 10 --region "$AWS_REGION" --query 'UserPools[?starts_with(Name, `receipt-search`)].{Name:Name,Id:Id}' --output table 2>/dev/null || echo "None")
if [[ "$USER_POOLS" == "None" || -z "$USER_POOLS" ]]; then
    print_status "✅ No Cognito User Pools found"
else
    print_error "❌ Found Cognito User Pools:"
    echo "$USER_POOLS"
fi

# Check SQS queues
print_status "Checking SQS queues..."
QUEUES=$(aws sqs list-queues --region "$AWS_REGION" --queue-name-prefix "receipt-search" --query 'QueueUrls' --output table 2>/dev/null || echo "None")
if [[ "$QUEUES" == "None" || -z "$QUEUES" ]]; then
    print_status "✅ No SQS queues found"
else
    print_error "❌ Found SQS queues:"
    echo "$QUEUES"
fi

# Check VPCs
print_status "Checking VPCs..."
VPCS=$(aws ec2 describe-vpcs --region "$AWS_REGION" --filters "Name=tag:Project,Values=receipt-search" --query 'Vpcs[].{VpcId:VpcId,State:State,Name:Tags[?Key==`Name`].Value|[0]}' --output table 2>/dev/null || echo "None")
if [[ "$VPCS" == "None" || -z "$VPCS" ]]; then
    print_status "✅ No VPCs found"
else
    print_error "❌ Found VPCs:"
    echo "$VPCS"
fi

echo ""
print_header "Cleanup Verification Complete"
print_status "If any resources were found above, you may need to delete them manually."
print_status "Most resources should be cleaned up automatically by the cleanup script."
