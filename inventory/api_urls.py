from django.urls import path

from .api_views import (
    CategoryListCreateAPIView,
    CategoryDetailAPIView,
    ProductListCreateAPIView,
    ProductDetailAPIView,
    StockTransactionListCreateAPIView,
    dashboard_api,
)


urlpatterns = [

    # Dashboard
    path(
        'dashboard/',
        dashboard_api,
        name='api-dashboard'
    ),

    # Categories
    path(
        'categories/',
        CategoryListCreateAPIView.as_view(),
        name='api-categories'
    ),

    path(
        'categories/<int:pk>/',
        CategoryDetailAPIView.as_view(),
        name='api-category-detail'
    ),

    # Products
    path(
        'products/',
        ProductListCreateAPIView.as_view(),
        name='api-products'
    ),

    path(
        'products/<int:pk>/',
        ProductDetailAPIView.as_view(),
        name='api-product-detail'
    ),

    # Stock Transactions
    path(
        'transactions/',
        StockTransactionListCreateAPIView.as_view(),
        name='api-transactions'
    ),
]