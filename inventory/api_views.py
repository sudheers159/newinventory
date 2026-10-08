from rest_framework import generics
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import F
from rest_framework.exceptions import ValidationError

from .models import Category, Product, StockTransaction
from .serializers import (
    CategorySerializer,
    ProductSerializer,
    StockTransactionSerializer
)


# -------------------------
# CATEGORY API
# -------------------------

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# -------------------------
# PRODUCT API
# -------------------------

class ProductListCreateAPIView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer


class ProductDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


# -------------------------
# STOCK TRANSACTION API
# -------------------------

class StockTransactionListCreateAPIView(
    generics.ListCreateAPIView
):
    queryset = StockTransaction.objects.all().order_by('-created_at')
    serializer_class = StockTransactionSerializer

    def perform_create(self, serializer):

        transaction = serializer.save()

        product = transaction.product

        if transaction.transaction_type == 'IN':

            product.quantity += transaction.quantity

        elif transaction.transaction_type == 'OUT':

            if product.quantity < transaction.quantity:

                transaction.delete()

                # raise ValueError(
                #     "Stock quantity is not enough."
                # )
                raise ValidationError(
                    "Stock quantity is not enough."
                )

            product.quantity -= transaction.quantity

        product.save()


# -------------------------
# DASHBOARD API
# -------------------------

@api_view(['GET'])
def dashboard_api(request):

    total_products = Product.objects.count()

    total_categories = Category.objects.count()

    low_stock_products = Product.objects.filter(
        quantity__lte=F('low_stock_limit')
    ).count()

    total_transactions = StockTransaction.objects.count()

    return Response({
        'total_products': total_products,
        'total_categories': total_categories,
        'low_stock_products': low_stock_products,
        'total_transactions': total_transactions,
    })