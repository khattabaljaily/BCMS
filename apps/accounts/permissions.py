"""
Flat list of all permission keys — mirrors PERMISSIONS dict in models.py.
"""

PERMISSIONS = [
    # المواعيد
    'appointments.view', 'appointments.add', 'appointments.edit', 'appointments.delete',
    # العملاء
    'clients.view', 'clients.add', 'clients.edit', 'clients.delete',
    # الخدمات
    'services.view', 'services.manage',
    # الفواتير ونقطة البيع
    'billing.view', 'billing.create', 'billing.void', 'billing.pos',
    # المنتجات والمخزون
    'products.view', 'products.manage',
    # الفريق
    'staff.view', 'staff.manage',
    # المتجر
    'store.view', 'store.manage',
    # المالية والحسابات
    'finance.view', 'finance.expenses', 'finance.client_payments',
    'finance.user_advances', 'finance.user_salaries',
    # التقارير
    'reports.view',
    # الإعدادات
    'settings.manage',
]
