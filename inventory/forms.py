from django import forms

from .models import Category, Product


class ProductChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, product):
        return f"{product.name} ({product.sku}) — Current: {product.quantity}"


class StockTransactionForm(forms.Form):
    product = ProductChoiceField(queryset=Product.objects.none())
    quantity = forms.IntegerField(min_value=1)
    note = forms.CharField(required=False, max_length=255)

    def __init__(self, *args, kind, **kwargs):
        super().__init__(*args, **kwargs)
        products = Product.objects.order_by("name")
        if kind == "OUT":
            products = products.filter(quantity__gt=0)
        self.fields["product"].queryset = products


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = (
            "name",
            "sku",
            "category",
            "subcategory",
            "quantity",
            "low_stock_limit",
        )
        labels = {"sku": "Dealer Details"}
        widgets = {
            "category": forms.Select(attrs={"id": "product-category"}),
            "subcategory": forms.Select(attrs={"id": "product-subcategory"}),
            "quantity": forms.NumberInput(attrs={"id": "product-quantity", "min": 0}),
            "low_stock_limit": forms.NumberInput(
                attrs={"id": "low-stock-limit", "min": 0}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].required = True
        self.fields["low_stock_limit"].required = False
        self.fields["subcategory"].widget.attrs["id"] = "product-subcategory"

        selected_category = None
        category_id = self.instance.category_id if not self.is_bound else None
        if category_id:
            selected_category = Category.objects.filter(pk=category_id).first()

        if not self.is_bound and not self.instance.pk:
            self.initial.setdefault(
                "low_stock_limit",
                2 if selected_category and selected_category.name == "Playing Card" else 5,
            )

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get("category")
        subcategory = cleaned_data.get("subcategory")
        if category and category.name in ("Playing Card", "Playing Cards"):
            if not subcategory:
                self.add_error("subcategory", "Choose a subcategory for Playing Card.")
        else:
            cleaned_data["subcategory"] = ""
        if cleaned_data.get("low_stock_limit") is None:
            cleaned_data["low_stock_limit"] = (
                2 if category and category.name == "Playing Card" else 5
            )
        return cleaned_data
