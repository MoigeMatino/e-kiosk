# Generated by Django 5.1.5 on 2025-02-13 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_remove_notification_user_alter_order_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=255, unique=True),
        ),
    ]
