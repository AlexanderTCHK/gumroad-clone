# Generated by Django 3.1.14 on 2022-01-03 10:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_auto_20220103_1534'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='active',
            new_name='published',
        ),
    ]