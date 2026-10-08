from rest_framework import serializers
from .models import Category, Product, StockTransaction


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(
        source='category.name',
        read_only=True
    )

    is_low_stock = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id',
            'name',
            'sku',
            'category',
            'category_name',
            'purchase_price',
            'selling_price',
            'quantity',
            'low_stock_limit',
            'created_at',
            'is_low_stock',
        ]


class StockTransactionSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source='product.name',
        read_only=True
    )

    class Meta:
        model = StockTransaction
        fields = [
            'id',
            'product',
            'product_name',
            'transaction_type',
            'quantity',
            'note',
            'created_at',
        ]