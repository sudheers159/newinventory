from django.db import migrations, models


def set_playing_card_stock_limits(apps, schema_editor):
    Category = apps.get_model("inventory", "Category")
    Product = apps.get_model("inventory", "Product")
    category_ids = Category.objects.filter(name="Playing Card").values_list(
        "id", flat=True
    )
    Product.objects.filter(
        category_id__in=category_ids,
        low_stock_limit=5,
    ).update(low_stock_limit=2)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0002_seed_product_categories"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="subcategory",
            field=models.CharField(
                blank=True,
                choices=[("5G", "5G"), ("4G", "4G")],
                max_length=2,
            ),
        ),
        migrations.RunPython(
            set_playing_card_stock_limits,
            migrations.RunPython.noop,
        ),
    ]
