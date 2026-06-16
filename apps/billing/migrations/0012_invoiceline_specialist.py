from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0011_invoice_number_unique_per_center'),
        ('staff', '0005_alter_specialist_center'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceline',
            name='specialist',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='invoice_lines',
                to='staff.specialist',
                verbose_name='مقدم الخدمة',
            ),
        ),
    ]
