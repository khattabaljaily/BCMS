from decimal import Decimal
from django.db import models
from apps.core.models import CenterMixin
from apps.clients.models import Client
from apps.services.models import Service


class Invoice(CenterMixin):
    PAYMENT = [
        ('cash',         'نقد'),
        ('card_or_bank', 'بطاقة أو بنك'),
        ('later',        'لاحقاً'),
    ]
    STATUS = [
        ('draft',     'مسودة'),
        ('paid',      'مدفوعة'),
        ('partial',   'مدفوعة جزئياً'),
        ('cancelled', 'ملغاة'),
    ]

    number      = models.CharField('رقم الفاتورة', max_length=50, unique=True)
    client      = models.ForeignKey(
        Client, on_delete=models.PROTECT,
        related_name='invoices', verbose_name='العميل',
        null=True, blank=True
    )
    appointment = models.OneToOneField(
        'appointments.Appointment', on_delete=models.CASCADE,
        null=True, blank=True, related_name='invoice', verbose_name='الموعد'
    )

    date = models.DateField('التاريخ', auto_now_add=True)

    subtotal        = models.DecimalField('قبل الخصم', max_digits=10, decimal_places=2, default=Decimal('0'))
    discount_amount = models.DecimalField('قيمة الخصم', max_digits=10, decimal_places=2, default=Decimal('0'))
    tax_amount      = models.DecimalField('الضريبة',    max_digits=10, decimal_places=2, default=Decimal('0'))
    total           = models.DecimalField('الإجمالي',   max_digits=10, decimal_places=2, default=Decimal('0'))
    paid_amount     = models.DecimalField('المدفوع',    max_digits=10, decimal_places=2, default=Decimal('0'))

    payment_method = models.CharField('طريقة الدفع', max_length=20, choices=PAYMENT, default='cash')
    status         = models.CharField('الحالة',      max_length=20, choices=STATUS,  default='draft')
    notes          = models.TextField('ملاحظات', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'invoices'
        ordering = ['-created_at']
        verbose_name = 'فاتورة'
        verbose_name_plural = 'الفواتير'

    def __str__(self):
        return self.number

    @property
    def remaining(self):
        return self.total - self.paid_amount

    @property
    def is_paid(self):
        return self.paid_amount >= self.total

    def recalculate(self):
        lines = list(self.lines.all())
        self.subtotal = sum(l.line_total for l in lines)
        self.total    = max(self.subtotal - self.discount_amount + self.tax_amount, Decimal('0'))
        self.save(update_fields=['subtotal', 'total'])

    def mark_paid(self, amount=None, method='cash'):
        self.paid_amount    = amount if amount is not None else self.total
        self.payment_method = method
        self.status         = 'paid' if self.paid_amount >= self.total else 'partial'
        self.save(update_fields=['paid_amount', 'payment_method', 'status'])
        


class InvoiceLine(models.Model):
    invoice      = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='lines')
    description  = models.CharField('الوصف', max_length=300)
    service      = models.ForeignKey(Service, on_delete=models.SET_NULL, null=True, blank=True)
    product      = models.ForeignKey('products.Product', on_delete=models.SET_NULL, null=True, blank=True)
    quantity         = models.DecimalField('الكمية',      max_digits=10, decimal_places=2, default=Decimal('1'))
    unit_price       = models.DecimalField('سعر الوحدة', max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField('خصم %',       max_digits=5,  decimal_places=2, default=Decimal('0'))
    line_total       = models.DecimalField('الإجمالي',   max_digits=10, decimal_places=2, default=Decimal('0'))

    class Meta:
        db_table = 'invoice_lines'

    def save(self, *args, **kwargs):
        gross = self.unit_price * self.quantity
        self.line_total = (gross - gross * self.discount_percent / Decimal('100')).quantize(Decimal('0.01'))
        super().save(*args, **kwargs)

