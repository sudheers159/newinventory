from django.contrib import admin
from django.urls import path
from inventory import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.dashboard, name="dashboard"),
    path("products/", views.products, name="products"),
    path("products/add/", views.add_product, name="add_product"),
    path("products/<int:pk>/edit/", views.edit_product, name="edit_product"),
    path("products/<int:pk>/delete/", views.delete_product, name="delete_product"),
    path("stock-in/", views.stock_in, name="stock_in"),
    path("stock-out/", views.stock_out, name="stock_out"),
]
