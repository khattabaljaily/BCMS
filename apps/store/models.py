from decimal import Decimal
from django.db import models
from apps.core.models import CenterMixin
from apps.services.models import Service
from apps.products.models import Product


class OnlineBooking(CenterMixin):
    """حجز موعد عبر المتجر الإلكتروني"""
    STATUS = [
        ('new',       'جديد — بانتظار التأكيد'),
        ('confirmed', 'مؤكد'),
        ('cancelled', 'ملغي'),
    ]

    client_name    = models.CharField('الاسم', max_length=200)
    client_phone   = models.CharField('رقم الهاتف', max_length=20)
    client_email   = models.EmailField('البريد', blank=True)
    service        = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    services       = models.ManyToManyField(Service, blank=True, related_name='online_bookings', verbose_name='الخدمات')
    preferred_date = models.DateField('التاريخ المفضل')
    preferred_time = models.TimeField('الوقت المفضل', null=True, blank=True)
    notes          = models.TextField('ملاحظات', blank=True)
    status         = models.CharField('الحالة', max_length=20, choices=STATUS, default='new')
    appointment    = models.OneToOneField(
        'appointments.Appointment', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='online_booking'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'online_bookings'
        ordering = ['-created_at']
        verbose_name = 'حجز إلكتروني'
        verbose_name_plural = 'الحجوزات الإلكترونية'

    def __str__(self):
        return f'{self.client_name} — {self.preferred_date}'


class StoreOrder(CenterMixin):
    """طلب شراء منتجات عبر المتجر"""
    STATUS = [
        ('pending',   'قيد المراجعة'),
        ('confirmed', 'مؤكد'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
    ]
    client_name    = models.CharField('الاسم', max_length=200)
    client_phone   = models.CharField('الهاتف', max_length=20)
    client_address = models.TextField('عنوان التوصيل', blank=True)
    total          = models.DecimalField('الإجمالي', max_digits=10, decimal_places=2, default=Decimal('0'))
    status         = models.CharField('الحالة', max_length=20, choices=STATUS, default='pending')
    notes          = models.TextField('ملاحظات', blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'store_orders'
        ordering = ['-created_at']
        verbose_name = 'طلب متجر'
        verbose_name_plural = 'طلبات المتجر'

    def recalculate(self):
        self.total = sum(i.line_total for i in self.items.all())
        self.save(update_fields=['total'])


class StoreOrderItem(models.Model):
    order      = models.ForeignKey(StoreOrder, on_delete=models.CASCADE, related_name='items')
    product    = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity   = models.PositiveIntegerField('الكمية', default=1)
    unit_price = models.DecimalField('سعر الوحدة', max_digits=10, decimal_places=2, default=Decimal('0'))
    line_total = models.DecimalField('الإجمالي',   max_digits=10, decimal_places=2, default=Decimal('0'))

    class Meta:
        db_table = 'store_order_items'

    def save(self, *args, **kwargs):
        self.line_total = (self.unit_price * self.quantity).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)
