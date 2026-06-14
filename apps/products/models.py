from decimal import Decimal
from django.db import models
from django.utils import timezone
from apps.core.models import CenterMixin


class ProductCategory(CenterMixin):
    name      = models.CharField('الاسم', max_length=100)
    order     = models.PositiveIntegerField('الترتيب')
    is_active = models.BooleanField('نشط', default=True)

    class Meta:
        db_table = 'product_categories'
        ordering = ['order', 'name']
        verbose_name = 'تصنيف منتج'
        verbose_name_plural = 'تصنيفات المنتجات'

    def __str__(self):
        return self.name


class Product(CenterMixin):
    category    = models.ForeignKey(
        ProductCategory, on_delete=models.PROTECT,
        related_name='products', verbose_name='التصنيف', null=True, blank=True
    )
    name        = models.CharField('الاسم', max_length=200)
    description = models.TextField('الوصف', blank=True)
    sku         = models.CharField('الرمز SKU', max_length=100, blank=True)

    price     = models.DecimalField('سعر البيع', max_digits=10, decimal_places=2)
    cost      = models.DecimalField('التكلفة',   max_digits=10, decimal_places=2)
    stock     = models.DecimalField('المخزون',   max_digits=10, decimal_places=2)
    min_stock = models.DecimalField('حد التنبيه', max_digits=10, decimal_places=2, default=Decimal('5'))

    image         = models.ImageField('الصورة', upload_to='products/', blank=True, null=True)
    is_active     = models.BooleanField('نشط', default=True)
    show_in_store = models.BooleanField('يظهر في المتجر', default=True)

    class Meta:
        db_table = 'products'
        ordering = ['name']
        verbose_name = 'منتج'
        verbose_name_plural = 'المنتجات'

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock <= self.min_stock


class StockMovement(CenterMixin):
    """Record stock changes for a product.

    `change` is positive for incoming stock (purchase/adjustment positive)
    and negative for outgoing (sales).
    """
    TYPE_CHOICES = [
        ('purchase',  'شراء'),
        ('sale',      'بيع'),
        ('adjustment','تعديل'),
        ('transfer',  'نقل'),
        ('reversal',  'عكس'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='stock_movements')
    change  = models.DecimalField('الكمية', max_digits=12, decimal_places=2)
    type    = models.CharField('النوع', max_length=20, choices=TYPE_CHOICES)
    reference = models.CharField('مرجع', max_length=200, blank=True)
    notes     = models.TextField('ملاحظات', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'stock_movements'
        ordering = ['-created_at']
        verbose_name = 'حركة مخزون'
        verbose_name_plural = 'حركات المخزون'

    def __str__(self):
        return f'{self.product.name} {self.change} ({self.type})'

    def save(self, *args, **kwargs):
        # on create, apply change to product stock
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            p = self.product
            p.stock = (p.stock or 0) + self.change
            p.save(update_fields=['stock'])

    def delete(self, *args, **kwargs):
        # revert change when deleted
        p = self.product
        p.stock = (p.stock or 0) - self.change
        p.save(update_fields=['stock'])
        super().delete(*args, **kwargs)

    @property
    def reference_display(self):
        if self.reference:
            if self.reference.startswith('invoice_'):
                return f'فاتورة {self.reference.split("_",1)[1]}'
            if self.reference.startswith('purchase_'):
                return f'مشتريات {self.reference.split("_",1)[1]}'
            return self.reference
        return '—'


class PurchaseInvoice(CenterMixin):
    STATUS  = [('active', 'نشطة'), ('cancelled', 'ملغاة')]
    PAYMENT = [('cash', 'نقد'), ('card_or_bank', 'بطاقة/بنك'), ('credit', 'آجل')]

    number         = models.CharField('الرقم', max_length=50, unique=True)
    supplier       = models.CharField('المورد', max_length=200, blank=True)
    date           = models.DateField('التاريخ', default=timezone.localdate)
    payment_method = models.CharField('طريقة الدفع', max_length=20, choices=PAYMENT, default='cash')
    total          = models.DecimalField('الإجمالي', max_digits=12, decimal_places=2)
    status         = models.CharField('الحالة', max_length=20, choices=STATUS, default='active')
    notes          = models.TextField('ملاحظات', blank=True)
    paid           = models.BooleanField('مدفوعة', default=False)
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'purchase_invoices'
        ordering = ['-id']
        verbose_name = 'فاتورة مشتريات'
        verbose_name_plural = 'فواتير المشتريات'

    def __str__(self):
        return self.number

    def recalculate(self):
        self.total = sum(ln.line_total for ln in self.lines.all()) or Decimal('0')
        self.save(update_fields=['total'])


class PurchaseInvoiceLine(models.Model):
    invoice   = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name='lines')
    product   = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='purchase_lines')
    quantity  = models.DecimalField('الكمية', max_digits=12, decimal_places=2)
    unit_cost = models.DecimalField('تكلفة الوحدة', max_digits=10, decimal_places=2)
    line_total = models.DecimalField('الإجمالي', max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'purchase_invoice_lines'

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_cost
        super().save(*args, **kwargs)
