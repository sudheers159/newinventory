from django.db import migrations


def add_product_categories(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    for name in ["Playing Card", "Device", "Camera"]:
        Category.objects.get_or_create(name=name)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(add_product_categories, migrations.RunPython.noop),
    ]
