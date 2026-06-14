from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0007_alter_product_cost_alter_product_stock_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='purchaseinvoice',
            options={
                'ordering': ['-id'],
                'verbose_name': 'فاتورة مشتريات',
                'verbose_name_plural': 'فواتير المشتريات',
            },
        ),
        migrations.AlterField(
            model_name='stockmovement',
            name='type',
            field=models.CharField(
                choices=[
                    ('purchase',  'شراء'),
                    ('sale',      'بيع'),
                    ('adjustment','تعديل'),
                    ('transfer',  'نقل'),
                    ('reversal',  'عكس'),
                ],
                max_length=20,
                verbose_name='النوع',
            ),
        ),
    ]
