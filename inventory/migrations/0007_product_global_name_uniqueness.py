from django.db import migrations, models


def rename_duplicate_product_names(apps, schema_editor):
    Product = apps.get_model("inventory", "Product")
    database = schema_editor.connection.alias
    manager = Product.objects.using(database)
    duplicate_names = list(
        manager.values("name")
        .annotate(count=models.Count("pk"))
        .filter(count__gt=1)
        .order_by("name")
        .values_list("name", flat=True)
    )
    existing_names = set(manager.values_list("name", flat=True))

    for duplicate_name in duplicate_names:
        products = list(
            manager.filter(name=duplicate_name)
            .select_related("category")
            .order_by("pk")
        )
        for product in products[1:]:
            category_name = (
                product.category.name if product.category_id else "Uncategorized"
            )
            suffix = (
                f" ({category_name[:32]} - {product.sku[:32]} - ID {product.pk})"
            )
            candidate = f"{duplicate_name[:150 - len(suffix)]}{suffix}"
            counter = 2
            while candidate in existing_names:
                suffix = (
                    f" ({category_name[:32]} - {product.sku[:32]} "
                    f"- ID {product.pk}-{counter})"
                )
                candidate = f"{duplicate_name[:150 - len(suffix)]}{suffix}"
                counter += 1

            product.name = candidate
            product.save(using=database, update_fields=["name"])
            existing_names.add(candidate)


class Migration(migrations.Migration):

    dependencies = [
        ("inventory", "0006_remove_product_unique_product_dealer_details_per_category"),
    ]

    operations = [
        migrations.RunPython(
            rename_duplicate_product_names,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="product",
            name="name",
            field=models.CharField(
                error_messages={"unique": "A product with this name already exists."},
                max_length=150,
                unique=True,
            ),
        ),
    ]
