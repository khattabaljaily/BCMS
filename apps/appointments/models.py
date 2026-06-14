"""
BCMS Appointments — المواعيد والجلسات
"""
from decimal import Decimal
from django.db import models
from apps.core.models import CenterMixin
from apps.clients.models import Client
from apps.services.models import Service, Package
from apps.staff.models import Specialist


class Appointment(CenterMixin):
    STATUS = [
        ('pending',     'قيد الانتظار'),
        ('confirmed',   'مؤكد'),
        ('in_progress', 'جارٍ التنفيذ'),
        ('completed',   'مكتمل'),
        ('cancelled',   'ملغي'),
        ('no_show',     'لم يحضر'),
    ]

    client     = models.ForeignKey(
        Client, on_delete=models.PROTECT,
        related_name='appointments', verbose_name='العميل',
        null=True, blank=True
    )
    specialist = models.ForeignKey(
        Specialist, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='appointments', verbose_name='الفنية/الفني'
    )
    package    = models.ForeignKey(
        Package, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='الباقة'
    )

    date       = models.DateField('التاريخ')
    start_time = models.TimeField('وقت البدء')
    end_time   = models.TimeField('وقت الانتهاء', null=True, blank=True)

    services = models.ManyToManyField(
        Service, through='AppointmentService',
        verbose_name='الخدمات', blank=True
    )

    status = models.CharField('الحالة', max_length=20, choices=STATUS, default='pending')
    notes  = models.TextField('ملاحظات', blank=True)

    total_price = models.DecimalField(
        'إجمالي السعر', max_digits=10, decimal_places=2
    )

    # زيارة بدون ملف عميل
    walk_in_name  = models.CharField('اسم الزائر', max_length=200, blank=True)
    walk_in_phone = models.CharField('هاتف الزائر', max_length=20, blank=True)

    # مصدر الحجز
    SOURCE = [('direct', 'مباشر'), ('store', 'المتجر'), ('phone', 'هاتف')]
    source = models.CharField('مصدر الحجز', max_length=20, choices=SOURCE, default='direct')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'appointments'
        ordering = ['-id']
        indexes = [
            models.Index(fields=['center', 'date']),
            models.Index(fields=['center', 'status']),
            models.Index(fields=['center', 'date', 'status']),
        ]
        verbose_name = 'موعد'
        verbose_name_plural = 'المواعيد'

    def __str__(self):
        name = self.client.name if self.client else self.walk_in_name or 'زائر'
        return f'{name} — {self.date} {self.start_time}'

    @property
    def client_display(self):
        if self.client:
            return self.client.name
        return self.walk_in_name or 'زائر'

    @property
    def client_phone_display(self):
        if self.client:
            return self.client.phone
        return self.walk_in_phone

    def recalculate_price(self):
        if self.package:
            self.total_price = self.package.price
        else:
            total = sum(
                s.unit_price
                for s in self.appointment_services.all()
            )
            self.total_price = total
        self.save(update_fields=['total_price'])


class AppointmentService(models.Model):
    appointment = models.ForeignKey(
        Appointment, on_delete=models.CASCADE,
        related_name='appointment_services'
    )
    service    = models.ForeignKey(Service, on_delete=models.PROTECT)
    unit_price = models.DecimalField('السعر', max_digits=10, decimal_places=2)
    specialist = models.ForeignKey(
        Specialist, on_delete=models.SET_NULL,
        null=True, blank=True
    )

    class Meta:
        db_table = 'appointment_services'

    def __str__(self):
        return self.service.name
