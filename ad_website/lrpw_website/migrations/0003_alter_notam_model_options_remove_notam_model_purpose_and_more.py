# Generated by Django 5.1.4 on 2025-02-17 18:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lrpw_website', '0002_alter_notam_model_end_date_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='notam_model',
            options={'verbose_name': 'NOTAM model', 'verbose_name_plural': 'NOTAM models'},
        ),
        migrations.RemoveField(
            model_name='notam_model',
            name='purpose',
        ),
        migrations.AddField(
            model_name='notam_model',
            name='ad_open',
            field=models.BooleanField(default=False),
        ),
    ]
