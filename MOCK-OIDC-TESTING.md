# Mock OIDC Testing Guide

## Quick Start

1. **Start Docker Desktop**
2. **Start mock OIDC server:**
   ```bash
   docker compose up -d mock-oidc
   ```
3. **Start dev server:**
   ```bash
   npm run dev
   ```
4. **Navigate to:** http://localhost:3000

## Testing Different Roles

When you click **"Sign in with Azure AD"** on the login page, you'll be redirected to the mock OIDC server at `http://localhost:8080/azure/authorize`.

The interactive form will appear with several fields. Fill them in based on the role you want to test:

### 1. Admin Role (Full Access)
```
subject: admin-001
name: Admin User
email: admin@sleepnumber.com
roles: ADMIN
```

### 2. Analyst Role (Manage Vendors & Assessments)
```
subject: analyst-001
name: Risk Analyst
email: analyst@sleepnumber.com
roles: ANALYST
```

### 3. Viewer Role (Read-Only Access)
```
subject: viewer-001
name: Read Only User
email: viewer@sleepnumber.com
roles: VIEWER
```

### 4. Vendor Role (Limited Vendor Access)
```
subject: vendor-001
name: Vendor User
email: vendor@sleepnumber.com
roles: VENDOR
```

## Role Permissions

| Role | Permissions |
|------|-------------|
| **ADMIN** | All permissions (full system access) |
| **ANALYST** | Create/Read/Update vendors, assessments, findings, reports, remediation |
| **VIEWER** | Read-only access to all resources |
| **VENDOR** | Read vendor info, upload documents, update remediation actions (own vendor only) |

## Testing Flow

1. Click **"Sign in with Azure AD"** on login page
2. Mock OIDC form appears - fill in the fields for your desired role
3. Click **Submit** on the mock OIDC form
4. You'll be redirected back to the application
5. Dashboard loads with permissions based on your role

## Troubleshooting

**"Cannot connect to Docker daemon"**
- Start Docker Desktop

**Mock OIDC not responding**
- Check container: `docker ps | grep mock-oidc`
- Restart: `docker compose restart mock-oidc`
- View logs: `docker logs tprm-mock-oidc`

**Wrong role assigned**
- Check the `roles` field value matches exactly: `ADMIN`, `ANALYST`, `VIEWER`, or `VENDOR`
- Roles are case-sensitive
