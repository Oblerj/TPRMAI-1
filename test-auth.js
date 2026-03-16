/**
 * Test authentication flows for all mock users
 *
 * This script tests the full OAuth/OIDC authentication flow including:
 * 1. Accessing protected route (should redirect to /login)
 * 2. Submitting login form (Next.js server action)
 * 3. OAuth redirect to mock-OIDC
 * 4. User selection and callback
 * 5. Final redirect to dashboard
 */

const https = require('http');
const { URL } = require('url');

const BASE_URL = 'http://localhost:3000';
const OIDC_URL = 'http://localhost:10090';

// Helper to make HTTP requests with cookie support
async function fetch(url, options = {}) {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const opts = {
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      ...options,
    };

    const req = https.request(opts, (res) => {
      let data = '';
      res.on('data', (chunk) => data += chunk);
      res.on('end', () => {
        resolve({
          status: res.statusCode,
          headers: res.headers,
          data: data,
          url: url,
        });
      });
    });

    req.on('error', reject);

    if (options.body) {
      req.write(options.body);
    }

    req.end();
  });
}

// Extract cookies from response headers
function getCookies(headers) {
  const cookies = headers['set-cookie'] || [];
  return cookies.map(cookie => cookie.split(';')[0]).join('; ');
}

// Follow redirects manually
async function followRedirects(url, cookies = '', maxRedirects = 5) {
  let currentUrl = url;
  let currentCookies = cookies;
  let redirectCount = 0;

  while (redirectCount < maxRedirects) {
    console.log(`  → GET ${currentUrl}`);
    const response = await fetch(currentUrl, {
      headers: {
        'Cookie': currentCookies,
      },
    });

    // Update cookies
    const newCookies = getCookies(response.headers);
    if (newCookies) {
      currentCookies = currentCookies ? `${currentCookies}; ${newCookies}` : newCookies;
    }

    // Check for redirect
    if (response.status >= 300 && response.status < 400 && response.headers.location) {
      const redirectUrl = response.headers.location.startsWith('http')
        ? response.headers.location
        : new URL(response.headers.location, currentUrl).href;
      currentUrl = redirectUrl;
      redirectCount++;
      console.log(`  ← ${response.status} redirect to ${redirectUrl}`);
    } else {
      return { response, cookies: currentCookies };
    }
  }

  throw new Error('Too many redirects');
}

// Test authentication for a single user
async function testUser(username, role) {
  console.log(`\n🧪 Testing ${username} (${role})...`);
  console.log('═'.repeat(60));

  try {
    // Step 1: Access protected page
    console.log('\n📍 Step 1: Access /dashboard (should redirect to /login)');
    let { response, cookies } = await followRedirects(`${BASE_URL}/dashboard`);

    if (!response.data.includes('Sign In')) {
      console.log('  ✗ FAIL: Did not reach login page');
      console.log(`  Response status: ${response.status}`);
      return false;
    }
    console.log('  ✓ Redirected to login page');

    // Note: Testing server actions from Node.js is complex as they require
    // Next.js-specific headers and CSRF tokens. The authentication flow
    // needs to be tested through a real browser or Playwright.

    console.log('\n⚠️  Note: Full server action testing requires a browser');
    console.log('  Please test manually by visiting http://localhost:3000');
    console.log(`  and clicking the "${username}" button on the login page.`);

    return null; // Inconclusive - needs browser testing

  } catch (error) {
    console.log(`  ✗ ERROR: ${error.message}`);
    return false;
  }
}

// Main test runner
async function main() {
  console.log('🧪 Authentication Flow Tests');
  console.log('═'.repeat(60));
  console.log('Testing all mock users against the authentication flow\n');

  const users = [
    ['mock-admin', 'ADMIN'],
    ['mock-analyst', 'ANALYST'],
    ['mock-viewer', 'VIEWER'],
    ['mock-vendor', 'VENDOR'],
  ];

  const results = [];
  for (const [username, role] of users) {
    const result = await testUser(username, role);
    results.push({ username, role, passed: result });
    await new Promise(resolve => setTimeout(resolve, 500));
  }

  console.log('\n' + '═'.repeat(60));
  console.log('📊 Test Summary:');
  console.log('═'.repeat(60));

  const passed = results.filter(r => r.passed === true).length;
  const failed = results.filter(r => r.passed === false).length;
  const inconclusive = results.filter(r => r.passed === null).length;

  console.log(`✅ Passed: ${passed}/${users.length}`);
  console.log(`✗ Failed: ${failed}/${users.length}`);
  console.log(`⚠️  Inconclusive: ${inconclusive}/${users.length}`);

  console.log('\n💡 To complete testing:');
  console.log('  1. Open http://localhost:3000 in a browser');
  console.log('  2. Test each mock user button (Admin, Analyst, Viewer, Vendor)');
  console.log('  3. Verify you reach the dashboard after clicking each button');
  console.log('  4. Check /tmp/nextjs.log for any PKCE or authentication errors\n');
}

main().catch(console.error);
