from decimal import Decimal
from django.db import models
from django.db.models import Sum
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
    amount = models.DecimalField('المبلغ', max_digits=12, decimal_places=2)
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
    amount = models.DecimalField('المبلغ', max_digits=12, decimal_places=2)
    method = models.CharField('طريقة الدفع', max_length=50, choices=PAYMENT_METHODS, default='cash')
    date = models.DateField('التاريخ', auto_now_add=True)
    treasury = models.ForeignKey(Treasury, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField('ملاحظات', blank=True)

    class Meta:
        db_table = 'expenses'
        ordering = ['-date']
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
    amount = models.DecimalField('المبلغ', max_digits=12, decimal_places=2)
    date = models.DateField('التاريخ', auto_now_add=True)
    created_at = models.DateTimeField('تاريخ الإنشاء', auto_now_add=True, null=True)
    method = models.CharField('طريقة الدفع', max_length=50, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField('الحالة', max_length=20, choices=STATUS, default='confirmed')
    notes = models.TextField('ملاحظات', blank=True)

    class Meta:
        db_table = 'client_payments'
        ordering = ['-date', '-created_at']
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
