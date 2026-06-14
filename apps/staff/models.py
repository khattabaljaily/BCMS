"""
BCMS Staff — الفريق / المتخصصون
"""
from django.db import models
from apps.core.models import CenterMixin
from apps.services.models import Service


class Specialist(CenterMixin):
    """فنية/فني تجميل"""
    name      = models.CharField('الاسم', max_length=200)
    phone     = models.CharField('الهاتف', max_length=20, blank=True)
    specialty = models.CharField('التخصص', max_length=200, blank=True)
    bio       = models.TextField('نبذة', blank=True)
    photo     = models.ImageField('الصورة', upload_to='staff/', blank=True, null=True)
    services  = models.ManyToManyField(
        Service, blank=True,
        verbose_name='الخدمات المتخصصة',
        related_name='specialists'
    )

    # التقويم
    color = models.CharField('اللون في التقويم', max_length=7, default='#6366f1')

    # أوقات العمل
    work_start   = models.TimeField('بداية الدوام', null=True, blank=True)
    work_end     = models.TimeField('نهاية الدوام', null=True, blank=True)
    working_days = models.JSONField('أيام العمل', default=list,
                                    help_text='قائمة أرقام الأيام: 0=أحد ... 6=سبت')

    is_active = models.BooleanField('نشط', default=True)
    order     = models.PositiveIntegerField('الترتيب')

    class Meta:
        db_table = 'specialists'
        ordering = ['order', 'name']
        verbose_name = 'متخصص'
        verbose_name_plural = 'الفريق'

    def __str__(self):
        return self.name

    @property
    def appointment_count(self):
        return self.appointments.filter(status='completed').count()
