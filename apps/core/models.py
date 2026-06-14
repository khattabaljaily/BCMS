"""
BCMS Core Models
Center (= Tenant), Settings, ServiceType, CenterMixin
"""
from django.db import models
from django.utils import timezone

DEFAULT_CURRENCY = 'SDG'
DEFAULT_TIMEZONE = 'Africa/Khartoum'
DEFAULT_COUNTRY  = 'SD'


class ServiceType(models.Model):
    """نوع مركز التجميل — صالون شعر، عيادة تجميل، مشغل أظافر ..."""
    name    = models.CharField('الاسم', max_length=100)
    icon    = models.CharField('الأيقونة', max_length=60, default='fas fa-spa')
    color   = models.CharField('اللون', max_length=7, default='#ec4899')
    description = models.TextField('الوصف', blank=True)
    is_active   = models.BooleanField('نشط', default=True)
    order       = models.PositiveIntegerField('الترتيب', default=0)

    class Meta:
        db_table = 'service_types'
        ordering = ['order', 'name']
        verbose_name = 'نوع المركز'
        verbose_name_plural = 'أنواع المراكز'

    def __str__(self):
        return self.name


class CenterQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)


class CenterManager(models.Manager):
    def get_queryset(self):
        return CenterQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


class Center(models.Model):
    """
    المركز / الصالون — وحدة الاشتراك الأساسية (Tenant).
    كل بيانات المركز معزولة تماماً.
    """
    PLANS = [
        ('trial',      'تجريبي'),
        ('starter',    'مبتدئ'),
        ('pro',        'احترافي'),
        ('enterprise', 'مؤسسات'),
    ]

    # هوية المركز
    name         = models.CharField('اسم المركز', max_length=200)
    slug         = models.SlugField('الرابط المختصر', max_length=200, unique=True)
    service_type = models.ForeignKey(
        ServiceType, on_delete=models.PROTECT,
        verbose_name='نوع المركز', related_name='centers'
    )
    logo    = models.ImageField('الشعار', upload_to='centers/logos/', blank=True, null=True)

    # التواصل
    phone   = models.CharField('رقم الهاتف', max_length=20, blank=True)
    email   = models.EmailField('البريد الإلكتروني', blank=True)
    address = models.TextField('العنوان', blank=True)
    city    = models.CharField('المدينة', max_length=100, blank=True)
    country = models.CharField('البلد (كود)', max_length=10, default=DEFAULT_COUNTRY)

    # الاشتراك
    plan         = models.CharField('الباقة', max_length=20, choices=PLANS, default='trial')
    plan_start   = models.DateField('بداية الاشتراك', default=timezone.now)
    plan_expires = models.DateField('نهاية الاشتراك', null=True, blank=True)
    is_active    = models.BooleanField('نشط', default=True)
    is_demo      = models.BooleanField('حساب تجريبي', default=False)

    # التفضيلات
    timezone = models.CharField('المنطقة الزمنية', max_length=50, default=DEFAULT_TIMEZONE)
    currency = models.CharField('العملة', max_length=3, default=DEFAULT_CURRENCY)
    language = models.CharField('اللغة', max_length=10, default='ar')

    # الحدود
    max_staff = models.IntegerField('عدد الموظفين', default=10)
    max_users = models.IntegerField('عدد المستخدمين', default=5)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CenterManager()

    class Meta:
        db_table = 'centers'
        ordering = ['-created_at']
        verbose_name = 'مركز'
        verbose_name_plural = 'المراكز'

    def __str__(self):
        return self.name

    @property
    def is_trial(self):
        return self.plan == 'trial'

    @property
    def is_expired(self):
        if self.plan_expires is None:
            return False
        return self.plan_expires < timezone.now().date()


class Settings(models.Model):
    """إعدادات المركز"""
    center = models.OneToOneField(
        Center, on_delete=models.CASCADE, related_name='settings',
        verbose_name='المركز'
    )

    # الفواتير
    invoice_color       = models.CharField('لون الفواتير', max_length=7, default='#ec4899')
    invoice_prefix      = models.CharField('بادئة الفاتورة', max_length=10, default='INV')
    invoice_next_number = models.PositiveIntegerField('الرقم التالي', default=1)
    invoice_footer      = models.TextField('تذييل الفاتورة', blank=True)
    show_tax_on_invoice = models.BooleanField('إظهار الضريبة', default=False)
    tax_percent         = models.DecimalField('نسبة الضريبة %', max_digits=5, decimal_places=2, default=0)

    # المواعيد
    booking_enabled      = models.BooleanField('الحجز الذاتي عبر المتجر', default=True)
    booking_advance_days = models.IntegerField('أقصى حجز مسبق (يوم)', default=30)
    slot_minutes         = models.IntegerField('مدة الفترة الزمنية (دقيقة)', default=30)
    work_start           = models.TimeField('بداية الدوام', null=True, blank=True)
    work_end             = models.TimeField('نهاية الدوام', null=True, blank=True)
    # 0=Sun,1=Mon,2=Tue,3=Wed,4=Thu,5=Fri,6=Sat — matches JS getDay()
    work_days            = models.CharField('أيام العمل', max_length=20, default='0,1,2,3,4')

    # المتجر
    store_enabled = models.BooleanField('تفعيل المتجر الإلكتروني', default=False)
    store_name    = models.CharField('اسم المتجر', max_length=200, blank=True)
    store_cover   = models.ImageField('صورة غلاف المتجر', upload_to='store/', blank=True, null=True)

    # نظام النقاط
    loyalty_enabled     = models.BooleanField('تفعيل نقاط الولاء', default=False)
    points_per_currency = models.IntegerField('نقاط لكل وحدة نقد', default=1)

    # التذكير
    reminder_enabled      = models.BooleanField('تفعيل التذكير', default=False)
    reminder_hours_before = models.IntegerField('تذكير قبل الموعد بـ (ساعة)', default=24)

    class Meta:
        db_table = 'center_settings'
        verbose_name = 'إعدادات'
        verbose_name_plural = 'إعدادات'

    def __str__(self):
        return f'إعدادات {self.center.name}'

    @property
    def work_days_list(self):
        """Return work_days as a list of ints, e.g. [0,1,2,3,4]."""
        try:
            return [int(d) for d in self.work_days.split(',') if d.strip().isdigit()]
        except Exception:
            return [0, 1, 2, 3, 4]

    def next_invoice_number(self):
        num = f'{self.invoice_prefix}-{self.invoice_next_number:05d}'
        self.invoice_next_number += 1
        self.save(update_fields=['invoice_next_number'])
        return num

    def delete(self, *args, **kwargs):
        """
        Ensure all related objects for this center are removed even if some FKs use PROTECT.
        Strategy: iterate over all models, delete objects that have a `center` FK to this Center.
        On ProtectedError, attempt to delete the blocking objects as well and retry.
        """
        from django.apps import apps
        from django.db import transaction
        from django.db.models.deletion import ProtectedError

        with transaction.atomic():
            # First pass: try deleting all models that have a direct `center` FK
            models = apps.get_models()
            for model in models:
                try:
                    # find a field named 'center' pointing to this Center model
                    fld = None
                    for f in model._meta.fields:
                        if f.name == 'center' and getattr(f, 'remote_field', None) is not None:
                            rel = f.remote_field.model
                            # rel may be a string or model class
                            if rel == Center or (isinstance(rel, str) and rel.split('.')[-1] == 'Center'):
                                fld = f
                                break
                    if not fld:
                        continue
                    qs = model.objects.filter(center=self)
                    if not qs.exists():
                        continue
                    try:
                        qs.delete()
                    except ProtectedError as e:
                        # attempt to delete blocking objects then retry
                        blocked = getattr(e, 'args', [None, None])[1] or []
                        for o in list(blocked):
                            try:
                                o.delete()
                            except Exception:
                                # if deleting blocker fails, re-raise to abort overall delete
                                raise
                        # retry
                        qs.delete()
                except Exception:
                    # Any unexpected exception should abort the transaction
                    raise

            # finally delete the center itself
            super().delete(*args, **kwargs)


class CenterBackup(models.Model):
    """نسخة احتياطية لبيانات مركز معين"""

    BACKUP_TYPES = (
        ('manual',      'يدوي'),
        ('auto',        'تلقائي'),
        ('pre_restore', 'نسخة أمان'),
    )
    STATUS_CHOICES = (
        ('completed',   'مكتمل'),
        ('failed',      'فشل'),
        ('in_progress', 'جاري'),
    )

    center      = models.ForeignKey(
        Center, on_delete=models.CASCADE,
        related_name='backups', verbose_name='المركز',
    )
    filename    = models.CharField('اسم الملف', max_length=255)
    file_path   = models.CharField('مسار الملف', max_length=500)
    file_size   = models.BigIntegerField('الحجم بالبايت', default=0)
    backup_type = models.CharField('نوع النسخة', max_length=20, choices=BACKUP_TYPES, default='manual')
    status      = models.CharField('الحالة', max_length=20, choices=STATUS_CHOICES, default='in_progress')
    notes       = models.TextField('ملاحظات', blank=True)
    created_at  = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True)

    class Meta:
        db_table = 'center_backups'
        verbose_name = 'نسخة احتياطية'
        verbose_name_plural = 'النسخ الاحتياطية'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.center.name} — {self.filename}"

    @property
    def file_exists(self):
        from pathlib import Path
        return Path(self.file_path).exists()

    @property
    def file_size_display(self):
        if self.status != 'completed':
            return '—'
        size = self.file_size
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class CenterMixin(models.Model):
    """قاعدة مشتركة لجميع نماذج البيانات المرتبطة بمركز"""
    center = models.ForeignKey(
        Center, on_delete=models.CASCADE,
        verbose_name='المركز', db_index=True
    )

    class Meta:
        abstract = True
