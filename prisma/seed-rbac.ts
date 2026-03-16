import { PrismaClient } from '@prisma/client'

const prisma = new PrismaClient()

// Define all resources and their CRUD actions
const resources = [
  'vendors',
  'risk_profiles',
  'risk_assessments',
  'documents',
  'risk_findings',
  'reports',
  'remediation_actions',
  'users',
  'roles',
  'prompts',
  'audit_trail',
  'notifications',
  'agents',
]

const actions = ['CREATE', 'READ', 'UPDATE', 'DELETE']

// Define role permissions
// ADMIN gets all permissions automatically (handled in code)
const rolePermissions: Record<string, { resource: string; actions: string[] }[]> = {
  ANALYST: [
    { resource: 'vendors', actions: ['CREATE', 'READ', 'UPDATE'] },
    { resource: 'risk_profiles', actions: ['CREATE', 'READ', 'UPDATE'] },
    { resource: 'risk_assessments', actions: ['CREATE', 'READ', 'UPDATE'] },
    { resource: 'documents', actions: ['CREATE', 'READ', 'UPDATE'] },
    { resource: 'risk_findings', actions: ['CREATE', 'READ', 'UPDATE'] },
    { resource: 'reports', actions: ['CREATE', 'READ', 'UPDATE'] },
    { resource: 'remediation_actions', actions: ['CREATE', 'READ', 'UPDATE'] },
    { resource: 'notifications', actions: ['READ', 'UPDATE'] },
    { resource: 'agents', actions: ['READ'] },
    { resource: 'audit_trail', actions: ['READ'] },
    { resource: 'prompts', actions: ['READ'] },
  ],
  VIEWER: [
    { resource: 'vendors', actions: ['READ'] },
    { resource: 'risk_profiles', actions: ['READ'] },
    { resource: 'risk_assessments', actions: ['READ'] },
    { resource: 'documents', actions: ['READ'] },
    { resource: 'risk_findings', actions: ['READ'] },
    { resource: 'reports', actions: ['READ'] },
    { resource: 'remediation_actions', actions: ['READ'] },
    { resource: 'notifications', actions: ['READ'] },
  ],
  VENDOR: [
    { resource: 'vendors', actions: ['READ'] }, // Only their own vendor
    { resource: 'documents', actions: ['CREATE', 'READ'] }, // Upload documents
    { resource: 'risk_findings', actions: ['READ'] }, // See findings for their vendor
    { resource: 'remediation_actions', actions: ['READ', 'UPDATE'] }, // Update remediation status
    { resource: 'notifications', actions: ['READ'] },
  ],
}

async function seedRBAC() {
  console.log('Seeding RBAC tables...')

  // Create all permissions
  console.log('Creating permissions...')
  for (const resource of resources) {
    for (const action of actions) {
      await prisma.permission.upsert({
        where: {
          resource_action: { resource, action },
        },
        update: {},
        create: {
          resource,
          action,
          description: `${action} ${resource}`,
        },
      })
    }
  }
  console.log(`Created ${resources.length * actions.length} permissions`)

  // Create roles
  console.log('Creating roles...')
  const roles = [
    { name: 'ADMIN', description: 'Full system access', isSystem: true },
    { name: 'ANALYST', description: 'Risk analysts - can manage vendors and assessments', isSystem: true },
    { name: 'VIEWER', description: 'Read-only access to risk data', isSystem: true },
    { name: 'VENDOR', description: 'External vendor users - limited access to their own data', isSystem: true },
  ]

  for (const role of roles) {
    await prisma.role.upsert({
      where: { name: role.name },
      update: { description: role.description },
      create: role,
    })
  }
  console.log(`Created ${roles.length} roles`)

  // Assign permissions to roles
  console.log('Assigning permissions to roles...')
  for (const [roleName, permissions] of Object.entries(rolePermissions)) {
    const role = await prisma.role.findUnique({ where: { name: roleName } })
    if (!role) continue

    for (const perm of permissions) {
      for (const action of perm.actions) {
        const permission = await prisma.permission.findUnique({
          where: { resource_action: { resource: perm.resource, action } },
        })
        if (!permission) continue

        await prisma.rolePermission.upsert({
          where: {
            roleId_permissionId: { roleId: role.id, permissionId: permission.id },
          },
          update: {},
          create: {
            roleId: role.id,
            permissionId: permission.id,
          },
        })
      }
    }
  }

  // Migrate existing users to use roleId
  console.log('Migrating existing users to RBAC...')
  const usersWithOldRole = await prisma.user.findMany({
    where: { roleId: null },
  })

  for (const user of usersWithOldRole) {
    // Try to map old role string to new Role table
    const oldRole = (user as any).role || 'ANALYST'
    const newRole = await prisma.role.findUnique({
      where: { name: oldRole },
    })

    if (newRole) {
      await prisma.user.update({
        where: { id: user.id },
        data: { roleId: newRole.id },
      })
      console.log(`  Migrated user ${user.email} to role ${newRole.name}`)
    }
  }

  console.log('RBAC seeding complete!')
}

// Run if executed directly
seedRBAC()
  .catch((e) => {
    console.error(e)
    process.exit(1)
  })
  .finally(async () => {
    await prisma.$disconnect()
  })

export { seedRBAC }
