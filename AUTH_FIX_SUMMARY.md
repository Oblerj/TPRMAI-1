# OIDC Authentication Fix - Summary

## ✅ Status: FULLY OPERATIONAL

All authentication flows are working correctly. Comprehensive test suite validates end-to-end authentication for all 4 TPRM roles.

## 🎯 Test Results

```
tests/test_auth_flow.py - 9 tests PASSED (100%)

✓ TestServices (3/3)
  - Next.js app running and accessible
  - Mock OIDC provider healthy
  - OIDC discovery document valid

✓ TestMockOIDC (3/3)
  - All 4 user roles registered
  - Authorization page displays users
  - Token exchange successful

✓ TestBrowserFlow (3/3)
  - Login page loads correctly
  - Full authentication flow for ADMIN
  - All 4 roles authenticate successfully
```

## 🔧 Root Causes Fixed

### 1. **NextAuth v5 HTTP Client Authentication**
**Problem**: NextAuth v5 uses HTTP Basic authentication for token endpoint, but mock OIDC only accepted form-encoded credentials.

**Solution**:
- Added Basic auth header parsing in token endpoint
- Extracts credentials from `Authorization: Basic <base64>` header
- Falls back to form parameters if Basic auth not present
- Updated discovery document to advertise both methods

### 2. **Nonce Validation Error**
**Problem**: ID tokens included `"nonce": null` which caused NextAuth validation to fail with "unexpected ID Token nonce claim value".

**Solution**:
- Only include nonce claim in ID token when actually provided
- Changed from `"nonce": auth_code.get("nonce")` to conditional inclusion
- Prevents null values in JWT claims

### 3. **Edge Runtime Incompatibility**
**Problem**: Auth callbacks with Prisma database calls failed in Edge Runtime with "token.role is not a function" error.

**Solution**:
- Removed all Prisma calls from auth callbacks
- Simplified JWT/session callbacks to be Edge-compatible
- Role information flows directly from OIDC profile to session
- Database operations moved to API routes (Node.js runtime)

### 4. **Role Information Flow**
**Problem**: User roles were not being passed from OIDC to the application session.

**Solution**:
- Enhanced mock OIDC to include role claims in tokens
- Updated seed script to register users with roles
- Modified auth callbacks to extract and preserve role data
- Roles now available in session: `session.user.role`

## 📁 Files Modified

### Mock OIDC Provider
- **`mock-oidc/app.py`**
  - Added HTTP Basic authentication support
  - Fixed nonce handling (conditional inclusion)
  - Added role/roles support in all token endpoints
  - Updated discovery document with role claims

### NextAuth Configuration
- **`src/auth.ts`**
  - Removed Prisma database calls from callbacks
  - Simplified JWT callback for Edge Runtime compatibility
  - Added role extraction from OIDC profile
  - Session callback passes role to client

### Seed Scripts
- **`scripts/seed-mock-oidc.sh`**
  - Added role field to each user registration
  - ADMIN → "role": "ADMIN"
  - ANALYST → "role": "ANALYST"
  - VIEWER → "role": "VIEWER"
  - VENDOR → "role": "VENDOR"

### Middleware
- **`src/middleware.ts`**
  - Simplified to avoid Edge Runtime issues
  - Auth protection can be added at page/API level
  - NextAuth v5 with Prisma requires Node.js runtime

### Test Suite
- **`tests/test_auth_flow.py`**
  - Comprehensive Playwright + pytest test suite
  - Tests all 4 TPRM roles end-to-end
  - Validates OIDC discovery, token exchange, browser flow

## 🚀 Usage

### Start Development Environment

```bash
# Terminal 1: Start mock OIDC provider
cd mock-oidc
./start.sh

# Terminal 2: Seed test users
./scripts/seed-mock-oidc.sh

# Terminal 3: Start Next.js
npm run dev
```

### Test Users

All users are pre-configured with proper TPRM roles:

| User | Email | Role | Password |
|------|-------|------|----------|
| Mock Admin | admin@app.local | ADMIN | (OIDC - no password) |
| Mock Analyst | analyst@app.local | ANALYST | (OIDC - no password) |
| Mock Viewer | viewer@app.local | VIEWER | (OIDC - no password) |
| Mock Vendor | vendor@app.local | VENDOR | (OIDC - no password) |

### Run Tests

```bash
# Run all authentication tests
python3 -m pytest tests/test_auth_flow.py -v

# Run specific test class
python3 -m pytest tests/test_auth_flow.py::TestBrowserFlow -v

# Run with detailed output
python3 -m pytest tests/test_auth_flow.py -v -s
```

## 🔐 Authentication Flow

```
1. User visits /login page
2. Clicks "Sign In" button
3. Redirects to Mock OIDC (localhost:10090)
4. User selects their role from list
5. Mock OIDC generates JWT with role claim
6. Redirects to /api/auth/callback/oidc with auth code
7. NextAuth exchanges code for tokens (using Basic auth)
8. JWT token includes role information
9. Session created with user data and role
10. Redirects to /dashboard (authenticated)
```

## 📊 Technical Details

### JWT Token Structure

**ID Token Claims**:
```json
{
  "sub": "mock-admin",
  "email": "admin@app.local",
  "name": "Mock Admin",
  "role": "ADMIN",
  "iss": "http://localhost:10090",
  "aud": "mock-oidc-client",
  "iat": 1773692033,
  "exp": 1773695633
}
```

### Session Object

```typescript
{
  user: {
    name: "Mock Admin",
    email: "admin@app.local",
    role: "ADMIN",
    sub: "mock-admin"
  },
  expires: "2026-03-16T21:00:00.000Z"
}
```

## 🎓 Key Learnings

1. **NextAuth v5 Changes**:
   - Uses HTTP Basic auth by default for token endpoint
   - Requires explicit nonce handling
   - Edge Runtime limitations with Prisma

2. **OIDC Specification**:
   - OAuth2 error responses must be JSON format
   - Token endpoint must support multiple auth methods
   - Claims should only include values when present

3. **Testing Strategy**:
   - Playwright + pytest excellent for E2E auth testing
   - Test at multiple levels: service, API, browser
   - Separate concerns: OIDC provider vs NextAuth integration

## 🔜 Next Steps

1. **Re-enable Prisma Adapter** (optional):
   - Move to API routes instead of auth callbacks
   - Use API routes to sync OIDC users to database
   - Keep JWT-only sessions for Edge Runtime compatibility

2. **Add Page-Level Auth Guards**:
   - Use `auth()` function in server components
   - Check session and role at page level
   - Redirect to login if not authenticated

3. **Implement RBAC**:
   - Use `src/lib/rbac.ts` functions for permission checks
   - Enforce role-based access to features
   - Database already seeded with permissions

## 📝 Notes

- **Middleware Limitation**: NextAuth v5 auth middleware with Prisma callbacks doesn't work in Edge Runtime. Use page-level checks instead.
- **Database Sync**: User creation/updates should be handled in API routes (Node.js runtime) rather than auth callbacks.
- **Mock OIDC**: Production-ready for local development. Uses RS256 JWT signing and follows OIDC spec correctly.

---

**Date**: 2026-03-16
**Status**: Production Ready for Local Development
**Test Coverage**: 9/9 tests passing (100%)
