#!/bin/bash

# Test authentication with Cognito
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Get Cognito configuration from Terraform
cd ../../infrastructure/terraform
COGNITO_USER_POOL_ID=$(terraform output -raw cognito_user_pool_id)
COGNITO_CLIENT_ID=$(terraform output -raw cognito_user_pool_client_id)
API_URL=$(terraform output -raw api_gateway_url)
cd - > /dev/null

print_status "Testing Cognito Authentication"
print_status "User Pool ID: $COGNITO_USER_POOL_ID"
print_status "Client ID: $COGNITO_CLIENT_ID"
print_status "API URL: $API_URL"
echo ""

# Test credentials
USERNAME="test@example.com"
PASSWORD="TestPassword123!"

print_status "1. Authenticating user: $USERNAME"

# Initiate auth
AUTH_RESPONSE=$(aws cognito-idp initiate-auth \
    --auth-flow USER_PASSWORD_AUTH \
    --auth-parameters USERNAME="$USERNAME",PASSWORD="$PASSWORD" \
    --client-id "$COGNITO_CLIENT_ID" \
    --region ap-southeast-1 \
    2>/dev/null || echo "ERROR")

if [[ "$AUTH_RESPONSE" == "ERROR" ]]; then
    print_error "Authentication failed"
    exit 1
fi

# Extract tokens
ACCESS_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.AuthenticationResult.AccessToken // empty')
ID_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.AuthenticationResult.IdToken // empty')
REFRESH_TOKEN=$(echo "$AUTH_RESPONSE" | jq -r '.AuthenticationResult.RefreshToken // empty')

if [[ -z "$ACCESS_TOKEN" ]]; then
    print_error "Failed to get access token"
    echo "Response: $AUTH_RESPONSE"
    exit 1
fi

print_success "Authentication successful!"
echo "Access Token: ${ACCESS_TOKEN:0:50}..."
echo "ID Token: ${ID_TOKEN:0:50}..."
echo ""

# Test API with token
print_status "2. Testing authenticated API calls"

# Test /auth/me endpoint
print_status "Testing /auth/me endpoint..."
ME_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$API_URL/api/v1/auth/me")

HTTP_CODE=$(echo "$ME_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$ME_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    print_success "✓ /auth/me: HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
else
    print_error "✗ /auth/me: HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
fi

echo ""

# Test /receipts endpoint
print_status "Testing /receipts endpoint..."
RECEIPTS_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$API_URL/api/v1/receipts")

HTTP_CODE=$(echo "$RECEIPTS_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$RECEIPTS_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    print_success "✓ /receipts: HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
else
    print_error "✗ /receipts: HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
fi

echo ""

# Test /search endpoint
print_status "Testing /search endpoint..."
SEARCH_RESPONSE=$(curl -s -w "\n%{http_code}" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    "$API_URL/api/v1/search/receipts?q=test")

HTTP_CODE=$(echo "$SEARCH_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$SEARCH_RESPONSE" | head -n -1)

if [[ "$HTTP_CODE" == "200" ]]; then
    print_success "✓ /search: HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
else
    print_error "✗ /search: HTTP $HTTP_CODE"
    echo "Response: $RESPONSE_BODY"
fi

echo ""

# Save tokens for later use
echo "ACCESS_TOKEN=\"$ACCESS_TOKEN\"" > /tmp/cognito_tokens.sh
echo "ID_TOKEN=\"$ID_TOKEN\"" >> /tmp/cognito_tokens.sh
echo "REFRESH_TOKEN=\"$REFRESH_TOKEN\"" >> /tmp/cognito_tokens.sh

print_success "Tokens saved to /tmp/cognito_tokens.sh for future use"
print_status "You can source this file to use the tokens in other scripts:"
print_status "source /tmp/cognito_tokens.sh"
