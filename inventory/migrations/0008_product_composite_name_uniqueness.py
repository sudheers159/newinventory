from django.db import migrations, models


def rename_4g_subcategory(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.filter(subcategory="4G").update(subcategory="4C")


def reverse_4g_subcategory(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.filter(subcategory="4C").update(subcategory="4G")


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0007_product_global_name_uniqueness"),
    ]

    operations = [
        migrations.RunPython(rename_4g_subcategory, reverse_4g_subcategory),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(max_length=150),
        ),
        migrations.AlterField(
            model_name="product",
            name="subcategory",
            field=models.CharField(
                blank=True,
                choices=[("5C", "5C"), ("5B", "5B"), ("4C", "4C")],
                max_length=2,
            ),
        ),
        migrations.AddConstraint(
            model_name="product",
            constraint=models.UniqueConstraint(
                fields=("name", "category", "subcategory"),
                name="unique_product_name_category_subcategory",
                violation_error_message=(
                    "A product with this name already exists in this "
                    "category and subcategory."
                ),
            ),
        ),
    ]
