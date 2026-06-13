"""
Central list of available permission keys for roles.
Used by the admin/role UI to render checkboxes and by views to parse submitted permissions.
"""

PERMISSIONS = [
    'billing.create',
    'billing.view',
    'billing.manage',
    'clients.view',
    'clients.create',
    'clients.manage',
    'appointments.view',
    'appointments.manage',
    'products.manage',
    'store.orders',
    'reports.view',
    'settings.manage',
    'users.manage',
]
