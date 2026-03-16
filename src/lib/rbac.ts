import prisma from '@/lib/db'

// Permission actions
export type PermissionAction = 'CREATE' | 'READ' | 'UPDATE' | 'DELETE'

// Resources that can be protected
export type Resource =
  | 'vendors'
  | 'risk_profiles'
  | 'risk_assessments'
  | 'documents'
  | 'risk_findings'
  | 'reports'
  | 'remediation_actions'
  | 'users'
  | 'roles'
  | 'prompts'
  | 'audit_trail'
  | 'notifications'
  | 'agents'

// Check if a user has a specific permission
export async function hasPermission(
  userId: string,
  resource: Resource,
  action: PermissionAction
): Promise<boolean> {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      role: {
        include: {
          permissions: {
            include: {
              permission: true,
            },
          },
        },
      },
    },
  })

  if (!user?.role) {
    return false
  }

  // ADMIN has all permissions
  if (user.role.name === 'ADMIN') {
    return true
  }

  return user.role.permissions.some(
    (rp) => rp.permission.resource === resource && rp.permission.action === action
  )
}

// Get all permissions for a user
export async function getUserPermissions(userId: string): Promise<{ resource: string; action: string }[]> {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: {
      role: {
        include: {
          permissions: {
            include: {
              permission: true,
            },
          },
        },
      },
    },
  })

  if (!user?.role) {
    return []
  }

  // ADMIN has all permissions
  if (user.role.name === 'ADMIN') {
    const allPermissions = await prisma.permission.findMany()
    return allPermissions.map((p) => ({ resource: p.resource, action: p.action }))
  }

  return user.role.permissions.map((rp) => ({
    resource: rp.permission.resource,
    action: rp.permission.action,
  }))
}

// Check permission by role name (useful for middleware)
export async function roleHasPermission(
  roleName: string,
  resource: Resource,
  action: PermissionAction
): Promise<boolean> {
  // ADMIN has all permissions
  if (roleName === 'ADMIN') {
    return true
  }

  const role = await prisma.role.findUnique({
    where: { name: roleName },
    include: {
      permissions: {
        include: {
          permission: true,
        },
      },
    },
  })

  if (!role) {
    return false
  }

  return role.permissions.some(
    (rp) => rp.permission.resource === resource && rp.permission.action === action
  )
}

// Get user's role name
export async function getUserRole(userId: string): Promise<string | null> {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    include: { role: true },
  })

  return user?.role?.name || null
}

// Middleware helper: require permission for API routes
export function requirePermission(resource: Resource, action: PermissionAction) {
  return async (userId: string): Promise<{ allowed: boolean; error?: string }> => {
    if (!userId) {
      return { allowed: false, error: 'Unauthorized: No user ID provided' }
    }

    const allowed = await hasPermission(userId, resource, action)
    if (!allowed) {
      return {
        allowed: false,
        error: `Forbidden: Missing ${action} permission for ${resource}`,
      }
    }

    return { allowed: true }
  }
}
