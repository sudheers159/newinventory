from django.db import migrations, models


def rename_4c_subcategory(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.filter(subcategory="4C").update(subcategory="4G")


def reverse_4g_subcategory(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.filter(subcategory="4G").update(subcategory="4C")


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0008_product_composite_name_uniqueness"),
    ]

    operations = [
        migrations.RunPython(rename_4c_subcategory, reverse_4g_subcategory),
        migrations.AlterField(
            model_name="product",
            name="subcategory",
            field=models.CharField(
                blank=True,
                choices=[("5C", "5C"), ("5B", "5B"), ("4G", "4G")],
                max_length=2,
            ),
        ),
    ]
