from django.db import migrations, models


def rename_legacy_playing_card_subcategory(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    Product.objects.filter(subcategory="5G").update(subcategory="5C")


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0003_product_subcategory"),
    ]

    operations = [
        migrations.RunPython(
            rename_legacy_playing_card_subcategory,
            migrations.RunPython.noop,
        ),
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
