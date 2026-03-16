# Authentication Testing Guide

## What Was Fixed

### Root Cause: OIDC Issuer Mismatch
The authentication failures for Mock Analyst, Viewer, and Vendor users were caused by a mismatch between the OIDC issuer URL in JWT tokens and the expected issuer URL in NextAuth configuration:

- **JWT Token Issuer**: `http://mock-oidc:10090` (Docker internal hostname)
- **NextAuth Expected Issuer**: `http://localhost:10090` (localhost)

When NextAuth received tokens with `iss: "http://mock-oidc:10090"`, it rejected them because it expected `iss: "http://localhost:10090"`. This manifested as PKCE code verifier parsing errors.

### Solution
Configure mock-OIDC to use `localhost:10090` for both internal and external URLs when running outside Docker:

```bash
export MOCK_OIDC_INTERNAL_BASE_URL="http://localhost:10090"
export MOCK_OIDC_EXTERNAL_BASE_URL="http://localhost:10090"
```

This ensures JWT tokens contain `iss: "http://localhost:10090"`, matching NextAuth's expectations.

## Quick Start

```bash
# Start development environment with correct configuration
./start-dev.sh

# Or manually:
# 1. Stop existing services
pkill -f "next dev"; pkill -f uvicorn

# 2. Start mock-OIDC with correct config
cd mock-oidc
export MOCK_OIDC_INTERNAL_BASE_URL="http://localhost:10090"
source venv/bin/activate
uvicorn app:app --host 0.0.0.0 --port 10090 &

# 3. Seed test users
cd ..
bash scripts/seed-mock-oidc.sh

# 4. Start Next.js
npm run dev
```

## Manual Testing Steps

### Test Each User Role

1. **Open the application**
   ```
   http://localhost:3000
   ```

2. **You should be redirected to login page**
   - URL: `http://localhost:3000/login`
   - Page shows: "AI TPRM System" with "Sign In" button

3. **Click "Sign In" button**
   - Should redirect to mock-OIDC login page
   - URL: `http://localhost:10090/authorize?...`
   - Page shows 4 user buttons

4. **Test each user by clicking their button:**

   | Button | Role | Expected Result |
   |--------|------|-----------------|
   | **Mock Admin** | ADMIN | ✓ Redirect to dashboard |
   | **Mock Analyst** | ANALYST | ✓ Redirect to dashboard |
   | **Mock Viewer** | VIEWER | ✓ Redirect to dashboard |
   | **Mock Vendor** | VENDOR | ✓ Redirect to dashboard |

5. **After clicking a user button:**
   - Should redirect through `/api/auth/callback/oidc`
   - Final destination: `http://localhost:3000/dashboard`
   - No "Server error" messages
   - No PKCE errors in logs

6. **Sign out and repeat for next user:**
   - Click user profile (top right)
   - Click "Sign Out"
   - Repeat from step 1 with different user

### Expected Success Indicators

✅ **All users authenticate successfully**
- No "Server error" messages
- No redirect loops
- Dashboard loads after authentication
- User role displayed correctly in UI

✅ **Clean logs**
```bash
# Check Next.js logs - should have no PKCE errors
tail -f /tmp/nextjs.log

# Should see:
# [Auth Profile] { sub: 'mock-analyst', ... role: 'ANALYST' }
# GET /dashboard 200
```

✅ **OIDC configuration correct**
```bash
curl -s http://localhost:10090/.well-known/openid-configuration | jq .issuer
# Should output: "http://localhost:10090"
```

### Common Issues

❌ **"Server error" on authentication**
- **Cause**: OIDC issuer mismatch
- **Fix**: Restart mock-OIDC with `MOCK_OIDC_INTERNAL_BASE_URL="http://localhost:10090"`
- **Verify**: `curl -s http://localhost:10090/.well-known/openid-configuration | jq .issuer`

❌ **PKCE code verifier parsing errors**
- **Cause**: Cookie/session state corruption OR issuer mismatch
- **Fix**:
  1. Clear browser cookies for localhost
  2. Verify OIDC issuer is set to localhost (not mock-oidc)
  3. Restart both services: `./start-dev.sh`

❌ **Mock Admin works but other users fail**
- **Cause**: Likely issuer mismatch or session interference
- **Fix**:
  1. Clear all browser cookies
  2. Verify each user is properly seeded: `curl -s http://localhost:10090/api/users | jq`
  3. Check that issuer matches in tokens

## Automated Testing

### Basic Flow Test
```bash
# Test protected route redirects
node test-auth.js
```

This tests:
- ✓ Protected routes redirect to /login
- ✓ Login page loads correctly
- ⚠️ Full OAuth flow requires browser (not automated)

### Future: Playwright Tests
For full end-to-end testing of the OAuth flow, consider adding Playwright:

```javascript
// tests/auth.spec.ts
test('All users can authenticate', async ({ page }) => {
  const users = ['Mock Admin', 'Mock Analyst', 'Mock Viewer', 'Mock Vendor']

  for (const user of users) {
    await page.goto('http://localhost:3000')
    await page.getByRole('button', { name: 'Sign In' }).click()
    await page.getByRole('button', { name: user }).click()
    await expect(page).toHaveURL(/.*dashboard/)
    // Sign out
    await page.getByRole('button', { name: user }).click()
    await page.getByText('Sign Out').click()
  }
})
```

## Verification Checklist

Before marking as complete:

- [ ] All 4 user roles authenticate successfully
- [ ] No PKCE errors in `/tmp/nextjs.log`
- [ ] No "Server error" messages in browser
- [ ] OIDC issuer is `http://localhost:10090`
- [ ] Dashboard loads correctly after auth
- [ ] User role displayed correctly in UI
- [ ] Sign out works correctly
- [ ] Can re-authenticate after sign out

## Architecture Notes

### Authentication Flow

```
1. User accesses /dashboard
   ↓
2. requireAuth() checks session
   ↓ (no session)
3. redirect('/login')
   ↓
4. User clicks "Sign In"
   ↓
5. Server action: signIn('oidc', { redirectTo: '/dashboard' })
   ↓
6. NextAuth initiates OAuth flow
   ↓
7. Redirect to mock-OIDC /authorize
   ↓
8. User selects mock user
   ↓
9. Mock-OIDC generates auth code
   ↓
10. Redirect to /api/auth/callback/oidc?code=...
    ↓
11. NextAuth exchanges code for tokens
    ↓
12. Validate JWT (issuer must match!)
    ↓
13. Create session + set cookies
    ↓
14. Redirect to /dashboard
    ↓
15. requireAuth() finds valid session
    ↓
16. ✅ Dashboard renders
```

### Key Files

- `src/auth.ts` - NextAuth configuration
- `src/lib/auth-guard.ts` - Server-side auth protection
- `src/app/login/actions.ts` - Sign in server action
- `mock-oidc/app.py` - Mock OIDC provider
- `.env` - OIDC configuration (OIDC_ISSUER_URL)

### Environment Variables

```bash
# NextAuth
AUTH_SECRET="9d0NNjRYCdlr0nOYNqMIbbVLDfMP+S1tTHyoIvtp7o8="
OIDC_ISSUER_URL="http://localhost:10090"
OIDC_CLIENT_ID="mock-oidc-client"
OIDC_CLIENT_SECRET="mock-oidc-secret"

# Mock-OIDC (must match OIDC_ISSUER_URL!)
MOCK_OIDC_INTERNAL_BASE_URL="http://localhost:10090"
MOCK_OIDC_EXTERNAL_BASE_URL="http://localhost:10090"
```

## Troubleshooting

### Debug Mode
Enable NextAuth debug logging:
```typescript
// src/auth.ts
debug: true, // Set to true temporarily
```

### View Raw Tokens
```bash
# Decode JWT from mock-OIDC
curl -s http://localhost:10090/token \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_CODE" \
  -d "redirect_uri=http://localhost:3000/api/auth/callback/oidc" \
  -d "client_id=mock-oidc-client" \
  -d "client_secret=mock-oidc-secret" \
  | jq -r .id_token \
  | cut -d. -f2 \
  | base64 -d \
  | jq
```

### Check Session
```typescript
// In any server component
import { auth } from '@/auth'

const session = await auth()
console.log('Session:', session)
```
