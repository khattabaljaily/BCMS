"""
BCMS Accounts — User model + Role-based permissions
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from apps.core.models import Center


# ── Permissions catalog ──────────────────────────────────────────────────
PERMISSIONS = {
    'appointments': {
        'view':   'عرض المواعيد',
        'add':    'إضافة موعد',
        'edit':   'تعديل موعد',
        'delete': 'حذف موعد',
    },
    'clients': {
        'view':   'عرض العملاء',
        'add':    'إضافة عميل',
        'edit':   'تعديل عميل',
        'delete': 'حذف عميل',
    },
    'services': {
        'view':   'عرض الخدمات',
        'manage': 'إدارة الخدمات والباقات',
    },
    'billing': {
        'view':   'عرض الفواتير',
        'create': 'إنشاء فاتورة',
        'void':   'إلغاء فاتورة',
        'pos':    'نقطة البيع (POS)',
    },
    'products': {
        'view':   'عرض المنتجات والمخزون',
        'manage': 'إدارة المنتجات والمخزون',
    },
    'staff': {
        'view':   'عرض الفريق',
        'manage': 'إدارة الفريق',
    },
    'store': {
        'view':   'عرض المتجر والحجوزات',
        'manage': 'إدارة المتجر',
    },
    'finance': {
        'view':            'عرض الخزينة والحسابات',
        'expenses':        'إدارة المصروفات',
        'client_payments': 'مدفوعات العملاء',
        'user_advances':   'سلف الموظفين',
        'user_salaries':   'رواتب الموظفين',
    },
    'reports': {
        'view': 'عرض التقارير',
    },
    'settings': {
        'manage': 'إدارة إعدادات الحساب',
    },
}


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra):
        user = self.model(username=username, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra)


class Role(models.Model):
    """دور / مجموعة صلاحيات داخل الحساب"""
    center      = models.ForeignKey(Center, on_delete=models.CASCADE, related_name='roles')
    name        = models.CharField('الاسم', max_length=100)
    permissions = models.JSONField('الصلاحيات', default=dict)
    is_default  = models.BooleanField('افتراضي للموظفين الجدد', default=False)

    class Meta:
        db_table = 'roles'
        unique_together = ['center', 'name']
        verbose_name = 'دور'
        verbose_name_plural = 'الأدوار'

    def __str__(self):
        return f'{self.name}'

    def has_perm(self, section, action):
        """role.has_perm('billing', 'create')"""
        return bool(self.permissions.get(f'{section}.{action}', False))


class User(AbstractBaseUser, PermissionsMixin):
    """موظف / مستخدم النظام"""
    center    = models.ForeignKey(
        Center, on_delete=models.CASCADE,
        null=True, blank=True, related_name='users', verbose_name='الحساب'
    )
    username  = models.CharField('اسم المستخدم', max_length=150, unique=True)
    full_name = models.CharField('الاسم الكامل', max_length=200)
    phone     = models.CharField('الهاتف', max_length=20, blank=True)
    email     = models.EmailField('البريد الإلكتروني', blank=True)
    role      = models.ForeignKey(
        Role, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='users', verbose_name='الدور'
    )
    avatar       = models.ImageField('الصورة', upload_to='avatars/', blank=True, null=True)
    base_salary  = models.DecimalField('الراتب الأساسي', max_digits=10, decimal_places=2, default=0)

    is_active    = models.BooleanField('نشط', default=True)
    is_staff     = models.BooleanField('موظف إداري', default=False)
    is_owner     = models.BooleanField('مالك الحساب', default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    last_login_at = models.DateTimeField(null=True, blank=True)

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['full_name']
    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'مستخدم'
        verbose_name_plural = 'المستخدمون'

    def __str__(self):
        return self.full_name or self.username

    def can(self, section, action='view'):
        """request.user.can('billing', 'create')"""
        if self.is_superuser or self.is_owner:
            return True
        if self.role:
            return self.role.has_perm(section, action)
        return False
