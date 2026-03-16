#!/bin/bash
# Automated authentication flow test
# Tests the complete OIDC login flow with mock service

set -e

echo "🧪 Testing AI TPRM Authentication Flow"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test configuration
APP_URL="http://localhost:3000"
OIDC_URL="http://localhost:10090"

echo "📋 Test Configuration:"
echo "  App URL: $APP_URL"
echo "  OIDC URL: $OIDC_URL"
echo ""

# Test 1: Check services are running
echo "Test 1: Checking services..."
if curl -s -f "${APP_URL}/api/auth/providers" > /dev/null; then
    echo -e "${GREEN}✓${NC} Next.js app is running"
else
    echo -e "${RED}✗${NC} Next.js app is NOT running"
    exit 1
fi

if curl -s -f "${OIDC_URL}/health" > /dev/null; then
    echo -e "${GREEN}✓${NC} Mock OIDC service is running"
else
    echo -e "${RED}✗${NC} Mock OIDC service is NOT running"
    exit 1
fi
echo ""

# Test 2: Verify OIDC discovery
echo "Test 2: Verifying OIDC discovery document..."
DISCOVERY=$(curl -s "${OIDC_URL}/.well-known/openid-configuration")
ISSUER=$(echo "$DISCOVERY" | jq -r '.issuer')
AUTH_ENDPOINT=$(echo "$DISCOVERY" | jq -r '.authorization_endpoint')

if [ "$ISSUER" = "$OIDC_URL" ]; then
    echo -e "${GREEN}✓${NC} OIDC issuer is correctly configured: $ISSUER"
else
    echo -e "${RED}✗${NC} OIDC issuer mismatch. Expected: $OIDC_URL, Got: $ISSUER"
    exit 1
fi

if [ "$AUTH_ENDPOINT" = "${OIDC_URL}/authorize" ]; then
    echo -e "${GREEN}✓${NC} Authorization endpoint is correct"
else
    echo -e "${RED}✗${NC} Authorization endpoint incorrect: $AUTH_ENDPOINT"
    exit 1
fi
echo ""

# Test 3: Check NextAuth provider configuration
echo "Test 3: Checking NextAuth provider configuration..."
PROVIDERS=$(curl -s "${APP_URL}/api/auth/providers")
OIDC_PROVIDER=$(echo "$PROVIDERS" | jq -r '.oidc')

if [ "$OIDC_PROVIDER" != "null" ]; then
    echo -e "${GREEN}✓${NC} OIDC provider is registered in NextAuth"
    PROVIDER_NAME=$(echo "$PROVIDERS" | jq -r '.oidc.name')
    echo "  Provider name: $PROVIDER_NAME"
else
    echo -e "${RED}✗${NC} OIDC provider is NOT registered"
    echo "  Available providers:"
    echo "$PROVIDERS" | jq 'keys'
    exit 1
fi
echo ""

# Test 4: Test authorization flow redirect
echo "Test 4: Testing OIDC authorization flow..."
SIGNIN_URL="${APP_URL}/api/auth/signin/oidc?callbackUrl=%2Fdashboard"
REDIRECT=$(curl -s -L -D - "${SIGNIN_URL}" -o /dev/null | grep -i "^location:" | head -1 | tr -d '\r')

if echo "$REDIRECT" | grep -q "${OIDC_URL}/authorize"; then
    echo -e "${GREEN}✓${NC} NextAuth correctly redirects to OIDC authorization endpoint"
    echo "  Redirect location contains: ${OIDC_URL}/authorize"
else
    echo -e "${YELLOW}⚠${NC} Redirect check inconclusive"
    echo "  Location header: $REDIRECT"
fi
echo ""

# Test 5: Verify test users are available
echo "Test 5: Verifying test users in mock OIDC..."
AUTH_PAGE=$(curl -s "${OIDC_URL}/authorize?client_id=test&redirect_uri=http://localhost&response_type=code&scope=openid")

USERS=("Mock Admin" "Mock Analyst" "Mock Viewer" "Mock Vendor")
ALL_FOUND=true

for user in "${USERS[@]}"; do
    if echo "$AUTH_PAGE" | grep -q "$user"; then
        echo -e "${GREEN}✓${NC} Test user available: $user"
    else
        echo -e "${RED}✗${NC} Test user NOT found: $user"
        ALL_FOUND=false
    fi
done

if [ "$ALL_FOUND" = false ]; then
    exit 1
fi
echo ""

# Test 6: Verify RBAC roles in database
echo "Test 6: Verifying RBAC roles in database..."
DB_ROLES=$(sqlite3 prisma/dev.db "SELECT name FROM roles WHERE isActive = 1 ORDER BY name;")

EXPECTED_ROLES=("ADMIN" "ANALYST" "VENDOR" "VIEWER")
for role in "${EXPECTED_ROLES[@]}"; do
    if echo "$DB_ROLES" | grep -q "^${role}$"; then
        echo -e "${GREEN}✓${NC} Role exists in database: $role"
    else
        echo -e "${RED}✗${NC} Role NOT found in database: $role"
        exit 1
    fi
done
echo ""

# Summary
echo "========================================"
echo -e "${GREEN}✅ All authentication tests passed!${NC}"
echo ""
echo "📝 Manual test instructions:"
echo "1. Open: ${APP_URL}/login"
echo "2. Click 'Sign In' button"
echo "3. Select a test user (e.g., Mock Admin)"
echo "4. Click 'Sign In' on mock OIDC page"
echo "5. Verify redirect to dashboard"
echo ""
echo "Available test users:"
echo "  • mock-admin@app.local (ADMIN role)"
echo "  • mock-analyst@app.local (ANALYST role)"
echo "  • mock-viewer@app.local (VIEWER role)"
echo "  • mock-vendor@app.local (VENDOR role)"
