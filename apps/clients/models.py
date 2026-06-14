"""
BCMS Clients — بيانات العميلات/العملاء
"""
from django.db import models
from django.db.models import Sum, Count
from apps.core.models import CenterMixin


class Client(CenterMixin):
    GENDER = [('f', 'أنثى'), ('m', 'ذكر')]

    name      = models.CharField('الاسم', max_length=200)
    phone     = models.CharField('رقم الهاتف', max_length=20)
    email     = models.EmailField('البريد الإلكتروني', blank=True)
    gender    = models.CharField('الجنس', max_length=5, choices=GENDER, default='f')
    birthdate = models.DateField('تاريخ الميلاد', null=True, blank=True)
    notes     = models.TextField('ملاحظات', blank=True)

    # مصدر التعريف
    REFERRAL_CHOICES = [
        ('walk_in',    'زيارة مباشرة'),
        ('referral',   'توصية'),
        ('social',     'وسائل التواصل'),
        ('website',    'الموقع الإلكتروني'),
        ('other',      'أخرى'),
    ]
    referral = models.CharField('مصدر التعريف', max_length=20, choices=REFERRAL_CHOICES, blank=True)

    # الولاء
    points = models.IntegerField('نقاط الولاء')

    # الحالة
    is_active = models.BooleanField('نشطة', default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'clients'
        ordering = ['name']
        unique_together = ['center', 'phone']
        verbose_name = 'عميل'
        verbose_name_plural = 'العملاء'

    def __str__(self):
        return f'{self.name}'

    @property
    def visit_count(self):
        return self.appointments.filter(status='completed').count()

    @property
    def total_spent(self):
        return self.invoices.filter(status='paid').aggregate(t=Sum('total'))['t'] or 0

    @property
    def due_amount(self):
        return self.invoices.exclude(status='paid').exclude(status='cancelled').aggregate(t=Sum('total'))['t'] or 0

    @property
    def last_visit(self):
        appt = self.appointments.filter(status='completed').order_by('-date').first()
        return appt.date if appt else None
