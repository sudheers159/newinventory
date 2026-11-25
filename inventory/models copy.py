from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name

class Product(models.Model):
    name = models.CharField(
        max_length=150,
    )
    sku = models.CharField(max_length=50)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    subcategory = models.CharField(
        max_length=2,
        choices=[("5C", "5C"), ("5B", "5B"), ("4G", "4G")],
        blank=True,
    )
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=0)
    low_stock_limit = models.PositiveIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("name", "category", "subcategory"),
                name="unique_product_name_category_subcategory",
                violation_error_message=(
                    "A product with this name already exists in this "
                    "category and subcategory."
                ),
            )
        ]

    def __str__(self): return f"{self.name} ({self.sku})"
    @property
    def is_low_stock(self): return self.quantity <= self.low_stock_limit

class StockTransaction(models.Model):
    IN = "IN"
    OUT = "OUT"
    TYPE_CHOICES = [(IN,"Stock In"),(OUT,"Stock Out")]
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=3, choices=TYPE_CHOICES)
    quantity = models.PositiveIntegerField()
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.product.name} - {self.transaction_type}"
