"""
Comprehensive authentication flow tests using Playwright and pytest.
Tests the complete OIDC authentication flow end-to-end.
"""
import pytest
import requests
import time
from playwright.sync_api import Page, expect

# Service URLs
APP_URL = "http://localhost:3000"
OIDC_URL = "http://localhost:10090"

# Test users
TEST_USERS = {
    "admin": {"sub": "mock-admin", "email": "admin@app.local", "name": "Mock Admin", "role": "ADMIN"},
    "analyst": {"sub": "mock-analyst", "email": "analyst@app.local", "name": "Mock Analyst", "role": "ANALYST"},
    "viewer": {"sub": "mock-viewer", "email": "viewer@app.local", "name": "Mock Viewer", "role": "VIEWER"},
    "vendor": {"sub": "mock-vendor", "email": "vendor@app.local", "name": "Mock Vendor", "role": "VENDOR"},
}


class TestServices:
    """Test that all required services are running."""

    def test_nextjs_app_running(self):
        """Verify Next.js app is accessible."""
        response = requests.get(f"{APP_URL}/api/auth/providers", timeout=10)
        assert response.status_code == 200, f"Next.js app not responding: {response.status_code}"
        data = response.json()
        assert "oidc" in data, "OIDC provider not registered in NextAuth"
        print(f"✓ Next.js app running at {APP_URL}")
        print(f"✓ OIDC provider registered: {data['oidc']['name']}")

    def test_mock_oidc_running(self):
        """Verify mock OIDC service is accessible."""
        response = requests.get(f"{OIDC_URL}/health", timeout=10)
        assert response.status_code == 200, f"Mock OIDC not responding: {response.status_code}"
        print(f"✓ Mock OIDC running at {OIDC_URL}")

    def test_oidc_discovery(self):
        """Verify OIDC discovery document is correct."""
        response = requests.get(f"{OIDC_URL}/.well-known/openid-configuration", timeout=10)
        assert response.status_code == 200

        discovery = response.json()
        assert discovery["issuer"] == OIDC_URL, f"Issuer mismatch: {discovery['issuer']}"
        assert discovery["authorization_endpoint"] == f"{OIDC_URL}/authorize"
        assert discovery["token_endpoint"] == f"{OIDC_URL}/token"
        assert discovery["userinfo_endpoint"] == f"{OIDC_URL}/userinfo"

        print(f"✓ OIDC discovery document valid")
        print(f"  Issuer: {discovery['issuer']}")
        print(f"  Authorization: {discovery['authorization_endpoint']}")
        print(f"  Token: {discovery['token_endpoint']}")


class TestMockOIDC:
    """Test mock OIDC service endpoints."""

    def test_users_registered(self):
        """Verify all test users are registered in mock OIDC."""
        response = requests.get(f"{OIDC_URL}/api/users", timeout=10)
        assert response.status_code == 200

        users = response.json()
        registered_subs = [u["sub"] for u in users]

        for user_key, user_data in TEST_USERS.items():
            assert user_data["sub"] in registered_subs, f"User {user_data['sub']} not registered"
            print(f"✓ User registered: {user_data['name']} ({user_data['email']})")

    def test_authorize_shows_users(self):
        """Verify authorization page shows user selection."""
        response = requests.get(
            f"{OIDC_URL}/authorize",
            params={
                "client_id": "mock-oidc-client",
                "redirect_uri": f"{APP_URL}/api/auth/callback/oidc",
                "response_type": "code",
                "scope": "openid email profile"
            },
            timeout=10
        )
        assert response.status_code == 200

        html = response.text
        for user_key, user_data in TEST_USERS.items():
            assert user_data["name"] in html, f"User {user_data['name']} not in authorization page"
            print(f"✓ Authorization page shows: {user_data['name']}")

    def test_authorize_and_token_exchange(self):
        """Test complete authorization code flow."""
        # Step 1: Get authorization code by posting to authorize endpoint
        auth_response = requests.post(
            f"{OIDC_URL}/authorize",
            data={
                "sub": "mock-admin",
                "redirect_uri": f"{APP_URL}/api/auth/callback/oidc",
                "client_id": "mock-oidc-client",
                "state": "test_state",
                "nonce": ""
            },
            allow_redirects=False,
            timeout=10
        )

        assert auth_response.status_code == 302, f"Expected redirect, got {auth_response.status_code}"
        location = auth_response.headers.get("location")
        assert "code=" in location, f"No authorization code in redirect: {location}"

        # Extract code from redirect URL
        code = location.split("code=")[1].split("&")[0]
        print(f"✓ Authorization code obtained: {code[:20]}...")

        # Step 2: Exchange code for tokens
        token_response = requests.post(
            f"{OIDC_URL}/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": f"{APP_URL}/api/auth/callback/oidc",
                "client_id": "mock-oidc-client",
                "client_secret": "mock-oidc-secret",
                "code_verifier": "test_verifier"  # PKCE parameter
            },
            timeout=10
        )

        assert token_response.status_code == 200, f"Token exchange failed: {token_response.status_code} - {token_response.text}"

        tokens = token_response.json()
        assert "access_token" in tokens, "No access_token in response"
        assert "id_token" in tokens, "No id_token in response"
        assert "token_type" in tokens, "No token_type in response"
        assert tokens["token_type"] == "Bearer", f"Wrong token_type: {tokens['token_type']}"

        print(f"✓ Token exchange successful")
        print(f"  Access token: {tokens['access_token'][:30]}...")
        print(f"  ID token: {tokens['id_token'][:30]}...")
        print(f"  Token type: {tokens['token_type']}")


class TestBrowserFlow:
    """Test authentication flow using browser automation."""

    @pytest.fixture(scope="function")
    def page(self, playwright):
        """Create a new browser page for each test."""
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()

    def test_login_page_loads(self, page: Page):
        """Verify login page loads correctly."""
        page.goto(f"{APP_URL}/login")

        # Check for login page elements
        expect(page.get_by_role("heading", name="AI TPRM System")).to_be_visible()
        expect(page.locator("button:has-text('Sign In')")).to_be_visible()

        print(f"✓ Login page loads correctly")

    def test_full_authentication_flow_admin(self, page: Page):
        """Test complete authentication flow for ADMIN user."""
        print("\n=== Testing ADMIN Authentication Flow ===")

        # Step 1: Go to login page
        page.goto(f"{APP_URL}/login")
        print("✓ Navigated to login page")

        # Step 2: Click Sign In button
        page.locator("button:has-text('Sign In')").click()
        print("✓ Clicked Sign In button")

        # Step 3: Wait for redirect to mock OIDC
        page.wait_for_url(f"{OIDC_URL}/authorize**", timeout=10000)
        print(f"✓ Redirected to mock OIDC: {page.url}")

        # Step 4 & 5: Find and click Mock Admin button
        admin_button = page.get_by_role("button", name="Mock Admin")
        admin_button.wait_for(state="visible", timeout=10000)
        print("✓ User selection visible")
        admin_button.click(timeout=10000)
        print("✓ Selected Mock Admin user")

        # Step 6: Wait for redirect back to app (allow navigation to complete)
        page.wait_for_url(f"{APP_URL}/**", wait_until="domcontentloaded", timeout=10000)
        print(f"✓ Redirected back to app: {page.url}")

        # Step 7: Verify successful authentication
        # Should be on dashboard or not on login/error page
        current_url = page.url
        assert "/login" not in current_url, f"Still on login page: {current_url}"
        assert "/error" not in current_url, f"Redirected to error page: {current_url}"

        # Verify actually on a protected page (dashboard, vendors, etc.)
        assert any(path in current_url for path in ["/dashboard", "/vendors", "/agents"]), \
            f"Not on a protected page: {current_url}"

        print(f"✓ Authentication successful! Current page: {current_url}")

        # Take screenshot for verification
        page.screenshot(path="/tmp/auth_success.png")
        print("✓ Screenshot saved to /tmp/auth_success.png")

    def test_authentication_all_users(self, page: Page):
        """Test authentication for all user roles."""
        for user_key, user_data in TEST_USERS.items():
            print(f"\n=== Testing {user_data['role']} Authentication ({user_data['name']}) ===")

            # Navigate to login
            page.goto(f"{APP_URL}/login")

            # Click Sign In
            page.locator("button:has-text('Sign In')").click()

            # Wait for OIDC page
            page.wait_for_url(f"{OIDC_URL}/authorize**", timeout=10000)

            # Select user
            user_button = page.locator(f"button:has-text('{user_data['name']}')")
            expect(user_button).to_be_visible(timeout=5000)
            user_button.click()

            # Wait for redirect
            page.wait_for_url(f"{APP_URL}/**", timeout=30000)

            # Verify not on error/login page
            current_url = page.url
            assert "/login" not in current_url, f"{user_data['role']} stuck on login: {current_url}"
            assert "/error" not in current_url, f"{user_data['role']} error: {current_url}"

            print(f"✓ {user_data['role']} authentication successful")

            # Logout or clear cookies for next test
            page.context.clear_cookies()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
