"""
BCMS Services — ServiceCategory, Service, Package
"""
from decimal import Decimal
from django.db import models
from apps.core.models import CenterMixin


class ServiceCategory(CenterMixin):
    """تصنيف الخدمات — عناية بالشعر، بشرة، أظافر ..."""
    name      = models.CharField('الاسم', max_length=100)
    icon      = models.CharField('الأيقونة', max_length=60, default='fas fa-spa')
    color     = models.CharField('اللون', max_length=7, default='#ec4899')
    order     = models.PositiveIntegerField('الترتيب')
    is_active = models.BooleanField('نشط', default=True)

    class Meta:
        db_table = 'service_categories'
        ordering = ['order', 'name']
        verbose_name = 'تصنيف'
        verbose_name_plural = 'التصنيفات'

    def __str__(self):
        return self.name

    @property
    def active_services_count(self):
        return self.services.filter(is_active=True).count()


class Service(CenterMixin):
    """خدمة — قص شعر، صبغة، عناية بالبشرة ..."""
    category    = models.ForeignKey(
        ServiceCategory, on_delete=models.SET_NULL,
        related_name='services', verbose_name='التصنيف', null=True, blank=True
    )
    name        = models.CharField('اسم الخدمة', max_length=200)
    description = models.TextField('الوصف', blank=True)
    duration    = models.PositiveIntegerField('المدة (دقيقة)', default=60)
    price       = models.DecimalField('السعر', max_digits=10, decimal_places=2)
    cost        = models.DecimalField('التكلفة', max_digits=10, decimal_places=2)
    is_active   = models.BooleanField('نشط', default=True)
    show_in_store = models.BooleanField('يظهر في المتجر', default=True)
    order       = models.PositiveIntegerField('الترتيب')
    image       = models.ImageField('الصورة', upload_to='services/', blank=True, null=True)

    class Meta:
        db_table = 'services'
        ordering = ['category__order', 'order', 'name']
        verbose_name = 'خدمة'
        verbose_name_plural = 'الخدمات'

    def __str__(self):
        return self.name

    @property
    def duration_display(self):
        h, m = divmod(self.duration, 60)
        if h and m:
            return f'{h} س {m} د'
        if h:
            return f'{h} ساعة'
        return f'{m} دقيقة'


class Package(CenterMixin):
    """باقة خدمات — مجموعة خدمات بسعر خاص"""
    name        = models.CharField('اسم الباقة', max_length=200)
    description = models.TextField('الوصف', blank=True)
    price       = models.DecimalField('سعر الباقة', max_digits=10, decimal_places=2)
    services    = models.ManyToManyField(
        Service, through='PackageService',
        verbose_name='الخدمات المضمّنة'
    )
    is_active     = models.BooleanField('نشط', default=True)
    show_in_store = models.BooleanField('يظهر في المتجر', default=True)
    image         = models.ImageField('الصورة', upload_to='packages/', blank=True, null=True)

    class Meta:
        db_table = 'packages'
        verbose_name = 'باقة'
        verbose_name_plural = 'الباقات'

    def __str__(self):
        return self.name

    @property
    def original_price(self):
        return sum(ps.service.price for ps in self.package_services.select_related('service').all())

    @property
    def savings(self):
        return max(self.original_price - self.price, Decimal('0'))

    @property
    def total_duration(self):
        return sum(ps.service.duration for ps in self.package_services.select_related('service').all())


class PackageService(models.Model):
    package = models.ForeignKey(Package, on_delete=models.CASCADE, related_name='package_services')
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    order   = models.PositiveIntegerField()

    class Meta:
        db_table = 'package_services'
        ordering = ['order']
        unique_together = ['package', 'service']

    def __str__(self):
        return f'{self.package.name} → {self.service.name}'
