from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('core', '0001_initial'),
        ('clients', '0001_initial'),
        ('billing', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Treasury',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=120, verbose_name='اسم الخزينة')),
                ('initial_balance', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='الرصيد الابتدائي')),
                ('balance', models.DecimalField(decimal_places=2, default=0, max_digits=12, verbose_name='الرصيد الحالي')),
                ('center', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.center')),
            ],
            options={
                'verbose_name': 'خزينة',
                'verbose_name_plural': 'الخزائن',
                'db_table': 'treasuries',
            },
        ),
        migrations.CreateModel(
            name='TreasuryMovement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(choices=[('in', 'وارد'), ('out', 'منصرف'), ('initial', 'افتتاحية')], max_length=10, verbose_name='النوع')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='المبلغ')),
                ('reference', models.CharField(blank=True, max_length=200, verbose_name='مرجع')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('treasury', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movements', to='finance.treasury')),
            ],
            options={
                'verbose_name': 'حركة خزينة',
                'verbose_name_plural': 'حركات الخزينة',
                'db_table': 'treasury_movements',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Expense',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.CharField(max_length=120, verbose_name='الفئة')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='المبلغ')),
                ('date', models.DateField(auto_now_add=True, verbose_name='التاريخ')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('center', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.center')),
                ('treasury', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='finance.treasury')),
            ],
            options={
                'verbose_name': 'مصروف',
                'verbose_name_plural': 'مصروفات',
                'db_table': 'expenses',
                'ordering': ['-date'],
            },
        ),
        migrations.CreateModel(
            name='ClientPayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='المبلغ')),
                ('date', models.DateField(auto_now_add=True, verbose_name='التاريخ')),
                ('method', models.CharField(blank=True, max_length=50, verbose_name='طريقة الدفع')),
                ('notes', models.TextField(blank=True, verbose_name='ملاحظات')),
                ('center', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='core.center')),
                ('client', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='clients.client')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to='billing.invoice')),
            ],
            options={
                'verbose_name': 'دفعة عميل',
                'verbose_name_plural': 'مدفوعات العملاء',
                'db_table': 'client_payments',
                'ordering': ['-date'],
            },
        ),
    ]
