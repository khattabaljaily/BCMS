from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from apps.core.models import CenterMixin
from apps.clients.models import Client


class Treasury(CenterMixin):
    name = models.CharField('اسم الخزينة', max_length=120)
    initial_balance = models.DecimalField('الرصيد الابتدائي', max_digits=12, decimal_places=2, default=Decimal('0'))
    balance = models.DecimalField('الرصيد الحالي', max_digits=12, decimal_places=2, default=Decimal('0'))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'treasuries'
        verbose_name = 'خزينة'
        verbose_name_plural = 'الخزائن'

    def __str__(self):
        return self.name

    @property
    def short_name(self):
        """Return the base name without any center suffix (e.g. 'الخزينة الرئيسية')."""
        if isinstance(self.name, str) and ' - ' in self.name:
            return self.name.split(' - ')[0]
        return self.name

    def set_initial_balance(self, amount, notes=''):
        """
        Set the initial balance and record it as a statement (TreasuryMovement).
        If initial balance already exists, update it by creating an adjustment movement.
        """
        from django.db import transaction
        with transaction.atomic():
            # If there's already an initial balance, delete the previous initial movement
            if self.initial_balance != 0:
                self.movements.filter(type='initial').delete()
            
            # Update the initial_balance field
            self.initial_balance = Decimal(str(amount))
            self.save(update_fields=['initial_balance'])
            
            # Create the movement record
            TreasuryMovement.objects.create(
                treasury=self,
                type='initial',
                amount=Decimal(str(amount)),
                reference='الرصيد الافتتاحي',
                notes=notes or 'رصيد افتتاحي للخزينة'
            )
            
            # Recalculate balance
            total_in = self.movements.filter(type__in=['in', 'initial']).aggregate(t=Sum('amount'))['t'] or Decimal('0')
            total_out = self.movements.filter(type='out').aggregate(t=Sum('amount'))['t'] or Decimal('0')
            self.balance = total_in - total_out
            self.save(update_fields=['balance'])
            
            return self


class TreasuryMovement(models.Model):
    TYPE = [('in', 'وارد'), ('out', 'منصرف'), ('initial', 'افتتاحية')]
    treasury = models.ForeignKey(Treasury, on_delete=models.CASCADE, related_name='movements')
    type = models.CharField('النوع', max_length=10, choices=TYPE)
    amount = models.DecimalField('المبلغ', max_digits=12, decimal_places=2, default=Decimal('0'))
    reference = models.CharField('مرجع', max_length=200, blank=True)
    notes = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'treasury_movements'
        ordering = ['-created_at']
        verbose_name = 'حركة خزينة'
        verbose_name_plural = 'حركات الخزينة'

    def _recalc_treasury(self, treasury):
        total_in  = treasury.movements.filter(type__in=['in', 'initial']).aggregate(t=Sum('amount'))['t'] or Decimal('0')
        total_out = treasury.movements.filter(type='out').aggregate(t=Sum('amount'))['t'] or Decimal('0')
        treasury.balance = total_in - total_out
        treasury.save(update_fields=['balance'])

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self._recalc_treasury(self.treasury)

    def delete(self, *args, **kwargs):
        treasury = self.treasury
        super().delete(*args, **kwargs)
        self._recalc_treasury(treasury)


class Expense(CenterMixin):
    PAYMENT_METHODS = [
        ('cash', 'نقد'),
        ('card_or_bank', 'بطاقة أو بنك'),
    ]

    category = models.CharField('الفئة', max_length=120)
    amount = models.DecimalField('المبلغ', max_digits=12, decimal_places=2, default=Decimal('0'))
    method = models.CharField('طريقة الدفع', max_length=50, choices=PAYMENT_METHODS, default='cash')
    date = models.DateField('التاريخ', default=timezone.localdate)
    treasury = models.ForeignKey(Treasury, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField('ملاحظات', blank=True)

    class Meta:
        db_table = 'expenses'
        ordering = ['-id']
        verbose_name = 'مصروف'
        verbose_name_plural = 'مصروفات'

    def __str__(self):
        return f"{self.category} — {self.amount}"


class ClientPayment(CenterMixin):
    PAYMENT_METHODS = [
        ('cash', 'نقد'),
        ('card_or_bank', 'بطاقة أو بنك'),
    ]
    STATUS = [
        ('confirmed', 'مؤكدة'),
        ('cancelled', 'ملغاة'),
    ]

    invoice = models.ForeignKey('billing.Invoice', on_delete=models.CASCADE, related_name='payments')
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField('المبلغ', max_digits=12, decimal_places=2, default=Decimal('0'))
    date = models.DateField('التاريخ', default=timezone.localdate)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True, null=True)
    method = models.CharField('طريقة الدفع', max_length=50, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField('الحالة', max_length=20, choices=STATUS, default='confirmed')
    notes = models.TextField('ملاحظات', blank=True)

    class Meta:
        db_table = 'client_payments'
        ordering = ['-id']
        verbose_name = 'دفعة عميل'
        verbose_name_plural = 'مدفوعات العملاء'

    def __str__(self):
        return f"{self.client or self.invoice.client} — {self.amount}"

    def cancel(self):
        if self.status == 'cancelled':
            return
        from django.db import transaction
        with transaction.atomic():
            if self.invoice:
                self.invoice.paid_amount = max(self.invoice.paid_amount - self.amount, Decimal('0'))
                if self.invoice.paid_amount >= self.invoice.total:
                    self.invoice.status = 'paid'
                elif self.invoice.paid_amount > 0:
                    self.invoice.status = 'partial'
                else:
                    self.invoice.status = 'draft'
                self.invoice.save(update_fields=['paid_amount', 'status'])
            self.status = 'cancelled'
            self.save(update_fields=['status'])


# ── الرواتب والسلف ────────────────────────────────────────────────────────────

class Advance(CenterMixin):
    """سلفة لمقدم الخدمة"""
    STATUS = [
        ('pending',   'قائمة'),
        ('deducted',  'مخصومة'),
        ('cancelled', 'ملغاة'),
    ]

    specialist     = models.ForeignKey('staff.Specialist', on_delete=models.CASCADE,
                                       related_name='advances', verbose_name='مقدم الخدمة')
    amount         = models.DecimalField('المبلغ', max_digits=10, decimal_places=2)
    date           = models.DateField('التاريخ', default=timezone.localdate)
    treasury       = models.ForeignKey(Treasury, on_delete=models.SET_NULL,
                                       null=True, blank=True, verbose_name='الخزينة')
    status         = models.CharField('الحالة', max_length=20, choices=STATUS, default='pending')
    salary_payment = models.ForeignKey('SalaryPayment', on_delete=models.SET_NULL,
                                       null=True, blank=True, related_name='advance_items',
                                       verbose_name='كشف الراتب')
    notes          = models.TextField('ملاحظات', blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'advances'
        ordering = ['-created_at']
        verbose_name = 'سلفة'
        verbose_name_plural = 'السلف'

    def __str__(self):
        return f"{self.specialist} — {self.amount}"

    def _movement_ref(self):
        return f'advance_{self.pk}'

    def _record_outflow(self):
        if not self.treasury:
            return
        TreasuryMovement.objects.get_or_create(
            treasury=self.treasury,
            reference=self._movement_ref(),
            defaults=dict(
                type='out',
                amount=self.amount,
                notes=f'سلفة {self.specialist}',
            )
        )

    def _reverse_outflow(self):
        for tm in TreasuryMovement.objects.filter(reference=self._movement_ref()):
            TreasuryMovement.objects.create(
                treasury=tm.treasury,
                type='in',
                amount=tm.amount,
                reference=f'rev_{tm.reference}',
                notes=f'إلغاء سلفة {self.specialist}',
            )

    def cancel(self):
        if self.status == 'cancelled':
            return
        from django.db import transaction
        with transaction.atomic():
            self._reverse_outflow()
            self.status = 'cancelled'
            self.save(update_fields=['status'])


class SalaryPayment(CenterMixin):
    """كشف راتب شهري لمقدم الخدمة"""
    STATUS = [
        ('draft',     'مسودة'),
        ('paid',      'مدفوع'),
        ('cancelled', 'ملغى'),
    ]

    specialist        = models.ForeignKey('staff.Specialist', on_delete=models.CASCADE,
                                          related_name='salary_payments', verbose_name='مقدم الخدمة')
    period_start      = models.DateField('من')
    period_end        = models.DateField('إلى')

    base_salary       = models.DecimalField('الراتب الأساسي', max_digits=10, decimal_places=2, default=Decimal('0'))
    commission_amount = models.DecimalField('العمولة', max_digits=10, decimal_places=2, default=Decimal('0'))
    bonus             = models.DecimalField('الحوافز', max_digits=10, decimal_places=2, default=Decimal('0'))
    advances_deducted = models.DecimalField('السلف المخصومة', max_digits=10, decimal_places=2, default=Decimal('0'))
    deductions        = models.DecimalField('خصومات أخرى', max_digits=10, decimal_places=2, default=Decimal('0'))
    deductions_notes  = models.TextField('تفاصيل الخصومات', blank=True)

    treasury          = models.ForeignKey(Treasury, on_delete=models.SET_NULL,
                                          null=True, blank=True, verbose_name='الخزينة')
    status            = models.CharField('الحالة', max_length=20, choices=STATUS, default='draft')
    notes             = models.TextField('ملاحظات', blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'salary_payments'
        ordering = ['-period_start', '-created_at']
        verbose_name = 'كشف راتب'
        verbose_name_plural = 'كشوف الرواتب'

    def __str__(self):
        return f"{self.specialist} — {self.period_start}"

    @property
    def total_due(self):
        return (
            self.base_salary
            + self.commission_amount
            + self.bonus
            - self.advances_deducted
            - self.deductions
        )

    def _movement_ref(self):
        return f'salary_{self.pk}'

    def _record_outflow(self):
        if not self.treasury or self.total_due <= 0:
            return
        TreasuryMovement.objects.get_or_create(
            treasury=self.treasury,
            reference=self._movement_ref(),
            defaults=dict(
                type='out',
                amount=self.total_due,
                notes=f'راتب {self.specialist} {self.period_start}',
            )
        )

    def _reverse_outflow(self):
        for tm in TreasuryMovement.objects.filter(reference=self._movement_ref()):
            TreasuryMovement.objects.create(
                treasury=tm.treasury,
                type='in',
                amount=tm.amount,
                reference=f'rev_{tm.reference}',
                notes=f'إلغاء راتب {self.specialist} {self.period_start}',
            )

    def pay(self):
        if self.status != 'draft':
            return
        from django.db import transaction
        with transaction.atomic():
            self.status = 'paid'
            self.save(update_fields=['status'])
            self._record_outflow()
            # mark linked advances as deducted
            self.advance_items.filter(status='pending').update(status='deducted')

    def cancel(self):
        if self.status == 'cancelled':
            return
        from django.db import transaction
        with transaction.atomic():
            self._reverse_outflow()
            # restore advances to pending
            self.advance_items.filter(status='deducted').update(
                status='pending', salary_payment=None
            )
            self.status = 'cancelled'
            self.save(update_fields=['status'])
