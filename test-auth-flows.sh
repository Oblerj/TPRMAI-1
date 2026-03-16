#!/bin/bash

# Test all 4 mock users authentication flows
# This script tests authentication for Admin, Analyst, Viewer, and Vendor users

BASE_URL="http://localhost:3000"
COOKIE_JAR="/tmp/auth-test-cookies.txt"

echo "🧪 Testing Authentication Flows for All Users"
echo "=============================================="
echo ""

# Function to test a user login flow
test_user() {
    local user=$1
    local expected_role=$2

    echo "Testing $user ($expected_role role)..."

    # Clear cookies
    rm -f "$COOKIE_JAR"

    # Step 1: Access protected page (should redirect to login)
    echo "  → Accessing /dashboard (should redirect to /login)"
    RESPONSE=$(curl -s -L -c "$COOKIE_JAR" -b "$COOKIE_JAR" -w "\n%{http_code}" "$BASE_URL/dashboard")
    HTTP_CODE=$(echo "$RESPONSE" | tail -1)

    if [[ ! "$RESPONSE" =~ "Sign In" ]]; then
        echo "  ✗ FAIL: Did not redirect to login page"
        return 1
    fi
    echo "  ✓ Redirected to login page"

    # Step 2: Click sign in button (initiates OIDC flow)
    echo "  → Initiating OIDC authentication flow"
    AUTH_URL=$(curl -s -L -c "$COOKIE_JAR" -b "$COOKIE_JAR" -w "\n%{url_effective}" "$BASE_URL/api/auth/signin/oidc" | tail -1)

    if [[ ! "$AUTH_URL" =~ "localhost:10090" ]]; then
        echo "  ✗ FAIL: Did not redirect to OIDC provider"
        return 1
    fi
    echo "  ✓ Redirected to OIDC provider"

    # Step 3: Select user on mock OIDC login form
    echo "  → Selecting user: $user"
    CALLBACK_URL=$(curl -s -L -c "$COOKIE_JAR" -b "$COOKIE_JAR" -w "\n%{url_effective}" -X POST \
        -d "sub=$user" \
        -d "redirect_uri=$BASE_URL/api/auth/callback/oidc" \
        -d "client_id=mock-oidc-client" \
        -d "state=" \
        -d "nonce=" \
        "http://localhost:10090/authorize" | tail -1)

    if [[ ! "$CALLBACK_URL" =~ "localhost:3000" ]]; then
        echo "  ✗ FAIL: Did not receive callback redirect"
        echo "  Callback URL: $CALLBACK_URL"
        return 1
    fi
    echo "  ✓ Received auth callback"

    # Step 4: Follow callback to complete authentication
    echo "  → Completing authentication callback"
    FINAL_RESPONSE=$(curl -s -L -c "$COOKIE_JAR" -b "$COOKIE_JAR" -w "\n%{http_code}\n%{url_effective}" "$CALLBACK_URL")
    HTTP_CODE=$(echo "$FINAL_RESPONSE" | tail -2 | head -1)
    FINAL_URL=$(echo "$FINAL_RESPONSE" | tail -1)

    # Check if we got an error page
    if echo "$FINAL_RESPONSE" | grep -q "Server error"; then
        echo "  ✗ FAIL: Server error during authentication"
        echo "  Final URL: $FINAL_URL"
        echo "  Check /tmp/nextjs.log for details"
        return 1
    fi

    # Check if we successfully reached dashboard
    if [[ "$FINAL_URL" =~ "/dashboard" ]]; then
        echo "  ✓ Successfully authenticated and redirected to /dashboard"
        echo "  ✅ PASS: $user authentication successful"
        return 0
    else
        echo "  ✗ FAIL: Did not reach dashboard"
        echo "  Final URL: $FINAL_URL"
        echo "  HTTP Code: $HTTP_CODE"
        return 1
    fi
}

# Test all users
PASS_COUNT=0
FAIL_COUNT=0

for user_data in "mock-admin:ADMIN" "mock-analyst:ANALYST" "mock-viewer:VIEWER" "mock-vendor:VENDOR"; do
    IFS=: read -r user role <<< "$user_data"
    echo ""
    if test_user "$user" "$role"; then
        ((PASS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
    echo ""
    sleep 1
done

# Summary
echo "=============================================="
echo "Test Summary:"
echo "  ✅ Passed: $PASS_COUNT/4"
echo "  ✗ Failed: $FAIL_COUNT/4"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo "🎉 All authentication tests passed!"
    exit 0
else
    echo "❌ Some tests failed. Check /tmp/nextjs.log for details"
    exit 1
fi
