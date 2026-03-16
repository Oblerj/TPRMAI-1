"""
Mock OIDC Provider for local development
Python 3.12 + FastAPI implementation following make-it pattern
"""
import os
import time
import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import FastAPI, Form, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Mock OIDC Provider")

# Environment configuration
EXTERNAL_BASE_URL = os.getenv("MOCK_OIDC_EXTERNAL_BASE_URL", "http://localhost:3007")
INTERNAL_BASE_URL = os.getenv("MOCK_OIDC_INTERNAL_BASE_URL", "http://localhost:3007")
ISSUER_URL = EXTERNAL_BASE_URL

# JWT signing key (for development only)
JWT_SECRET = "mock-oidc-secret-key-for-development-only"
JWT_ALGORITHM = "HS256"

# Pre-seeded test users mapped to TPRM roles
TEST_USERS = {
    "mock-admin": {
        "sub": "mock-admin",
        "email": "admin@app.local",
        "name": "Mock Admin",
        "role": "ADMIN",
        "preferred_username": "admin@app.local"
    },
    "mock-analyst": {
        "sub": "mock-analyst",
        "email": "analyst@app.local",
        "name": "Mock Analyst",
        "role": "ANALYST",
        "preferred_username": "analyst@app.local"
    },
    "mock-viewer": {
        "sub": "mock-viewer",
        "email": "viewer@app.local",
        "name": "Mock Viewer",
        "role": "VIEWER",
        "preferred_username": "viewer@app.local"
    },
    "mock-vendor": {
        "sub": "mock-vendor",
        "email": "vendor@app.local",
        "name": "Mock Vendor",
        "role": "VENDOR",
        "preferred_username": "vendor@app.local"
    }
}

# In-memory storage for authorization codes and tokens
auth_codes = {}
access_tokens = {}

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker"""
    return {"status": "healthy"}


@app.get("/.well-known/openid-configuration")
async def openid_configuration():
    """OpenID Connect discovery document"""
    return {
        "issuer": ISSUER_URL,
        "authorization_endpoint": f"{EXTERNAL_BASE_URL}/authorize",
        "token_endpoint": f"{INTERNAL_BASE_URL}/token",
        "userinfo_endpoint": f"{INTERNAL_BASE_URL}/userinfo",
        "jwks_uri": f"{INTERNAL_BASE_URL}/jwks",
        "response_types_supported": ["code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["HS256"],
        "scopes_supported": ["openid", "email", "profile"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "client_secret_basic"],
        "claims_supported": ["sub", "email", "name", "preferred_username", "role"]
    }


@app.get("/authorize", response_class=HTMLResponse)
async def authorize(
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    response_type: str = Query("code"),
    scope: str = Query("openid email profile"),
    state: Optional[str] = Query(None)
):
    """Authorization endpoint - shows login form"""

    # Generate HTML form with pre-populated test users
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock OIDC Login</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
                max-width: 500px;
                margin: 50px auto;
                padding: 20px;
                background: #f5f5f5;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            h2 {{
                margin-top: 0;
                color: #333;
            }}
            .user-option {{
                background: #f8f9fa;
                padding: 15px;
                margin: 10px 0;
                border-radius: 4px;
                border: 2px solid transparent;
                cursor: pointer;
                transition: all 0.2s;
            }}
            .user-option:hover {{
                border-color: #0066cc;
                background: #e7f3ff;
            }}
            .user-option input[type="radio"] {{
                margin-right: 10px;
            }}
            .user-name {{
                font-weight: 600;
                color: #333;
            }}
            .user-email {{
                font-size: 0.9em;
                color: #666;
            }}
            .user-role {{
                display: inline-block;
                background: #0066cc;
                color: white;
                padding: 2px 8px;
                border-radius: 3px;
                font-size: 0.8em;
                margin-left: 10px;
            }}
            button {{
                width: 100%;
                padding: 12px;
                background: #0066cc;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 16px;
                cursor: pointer;
                margin-top: 20px;
            }}
            button:hover {{
                background: #0052a3;
            }}
            .info {{
                background: #fff3cd;
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 20px;
                font-size: 0.9em;
                color: #856404;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔐 Mock OIDC Login</h2>
            <div class="info">
                This is a mock identity provider for local development. Select a test user to continue.
            </div>
            <form method="post" action="/authorize">
                <input type="hidden" name="client_id" value="{client_id}">
                <input type="hidden" name="redirect_uri" value="{redirect_uri}">
                <input type="hidden" name="response_type" value="{response_type}">
                <input type="hidden" name="scope" value="{scope}">
                <input type="hidden" name="state" value="{state or ''}">

                <div>
    """

    # Add radio buttons for each test user
    for idx, (username, user_data) in enumerate(TEST_USERS.items()):
        checked = "checked" if idx == 0 else ""
        html_content += f"""
                    <label class="user-option">
                        <input type="radio" name="username" value="{username}" {checked}>
                        <span class="user-name">{user_data['name']}</span>
                        <span class="user-role">{user_data['role']}</span>
                        <br>
                        <span class="user-email">{user_data['email']}</span>
                    </label>
        """

    html_content += """
                </div>
                <button type="submit">Sign In</button>
            </form>
        </div>
    </body>
    </html>
    """

    return HTMLResponse(content=html_content)


@app.post("/authorize")
async def authorize_post(
    username: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    response_type: str = Form("code"),
    scope: str = Form("openid email profile"),
    state: Optional[str] = Form(None)
):
    """Handle authorization form submission"""

    if username not in TEST_USERS:
        return HTMLResponse(content="Invalid user", status_code=400)

    # Generate authorization code
    auth_code = f"mock_code_{int(time.time())}_{username}"
    auth_codes[auth_code] = {
        "username": username,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "created_at": time.time()
    }

    # Redirect back to application with code
    redirect_url = f"{redirect_uri}?code={auth_code}"
    if state:
        redirect_url += f"&state={state}"

    return RedirectResponse(url=redirect_url, status_code=302)


@app.post("/token")
async def token(
    request: Request,
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None)
):
    """Token endpoint - exchange code for tokens"""

    if grant_type != "authorization_code":
        return JSONResponse(
            status_code=400,
            content={"error": "unsupported_grant_type"}
        )

    if code not in auth_codes:
        return JSONResponse(
            status_code=400,
            content={"error": "invalid_grant"}
        )

    auth_data = auth_codes[code]
    username = auth_data["username"]
    user_data = TEST_USERS[username]

    # Extract client_id from auth_data if not provided in form
    # NextAuth v5 may send credentials via Basic Auth or form body
    if not client_id:
        client_id = auth_data.get("client_id", "mock-oidc-client")

    # Generate tokens
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=1)

    id_token_payload = {
        "iss": ISSUER_URL,
        "sub": user_data["sub"],
        "aud": client_id,  # Must be client_id string, not None
        "exp": int(expires_at.timestamp()),
        "iat": int(now.timestamp()),
        "email": user_data["email"],
        "name": user_data["name"],
        "preferred_username": user_data["preferred_username"],
        "role": user_data["role"],
        "roles": user_data["role"]  # Support both singular and array
    }

    id_token = jwt.encode(id_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    access_token = f"mock_access_{int(time.time())}_{username}"

    access_tokens[access_token] = user_data

    # Clean up used authorization code
    del auth_codes[code]

    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,
        "id_token": id_token,
        "scope": auth_data["scope"]
    }


@app.get("/userinfo")
async def userinfo(request: Request):
    """UserInfo endpoint"""

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"error": "invalid_token"}
        )

    access_token = auth_header[7:]  # Remove "Bearer " prefix

    if access_token not in access_tokens:
        return JSONResponse(
            status_code=401,
            content={"error": "invalid_token"}
        )

    user_data = access_tokens[access_token]
    return {
        "sub": user_data["sub"],
        "email": user_data["email"],
        "name": user_data["name"],
        "preferred_username": user_data["preferred_username"],
        "role": user_data["role"]
    }


@app.get("/jwks")
async def jwks():
    """JWKS endpoint - returns public keys for token verification"""
    # For HS256 (symmetric), we don't publish keys
    # In production, use RS256 with actual public keys
    return {"keys": []}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10090)
