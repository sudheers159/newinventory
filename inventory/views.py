from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ProductForm, StockTransactionForm
from .models import Product, Category, StockTransaction


def product_form_context(title, p=None, form_data=None):
    categories = Category.objects.all()
    category_id = form_data.get("category") if form_data else (
        p.category_id if p else None
    )
    try:
        selected_category = categories.filter(pk=category_id).first() if category_id else None
    except (TypeError, ValueError):
        selected_category = None
    is_playing_card = bool(
        selected_category and selected_category.name == "Playing Card"
    )
    default_low_stock_limit = 2 if is_playing_card else 5
    form_values = {
        "name": p.name if p else "",
        "sku": p.sku if p else "",
        "purchase_price": p.purchase_price if p else 0,
        "selling_price": p.selling_price if p else 0,
        "quantity": p.quantity if p else 0,
        "low_stock_limit": (
            p.low_stock_limit if p else default_low_stock_limit
        ),
        "subcategory": p.subcategory if p else "",
    }
    if form_data:
        for field in form_values:
            if field in form_data:
                form_values[field] = form_data[field]
    return {
        "categories": categories,
        "p": p,
        "title": title,
        "form_values": form_values,
        "selected_category_id": selected_category.pk if selected_category else None,
        "default_low_stock_limit": default_low_stock_limit,
    }


@login_required
def dashboard(request):
    products = Product.objects.all()
    context = {
        "product_count": products.count(),
        "products_in_stock": products.filter(quantity__gt=0).count(),
        "stock_total": products.aggregate(x=Sum("quantity"))["x"] or 0,
        "stock_in_total": StockTransaction.objects.filter(
            transaction_type=StockTransaction.IN
        ).aggregate(x=Sum("quantity"))["x"] or 0,
        "products_sold": StockTransaction.objects.filter(
            transaction_type=StockTransaction.OUT
        ).values("product_id").distinct().count(),
        "stock_out_total": StockTransaction.objects.filter(
            transaction_type=StockTransaction.OUT
        ).aggregate(x=Sum("quantity"))["x"] or 0,
        "low_stock": products.filter(quantity__lte=F("low_stock_limit")).count(),
        "categories": Category.objects.count(),
        "recent": StockTransaction.objects.select_related("product")[:8],
    }
    return render(request, "dashboard.html", context)

@login_required
def products(request):
    q = request.GET.get("q","").strip()
    qs = Product.objects.select_related("category").all()
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(sku__icontains=q)
    return render(request, "products.html", {"products": qs, "q": q})

@login_required
def add_product(request):
    if request.method == "POST":
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully.")
            return redirect("products")
    else:
        form = ProductForm()
    context = product_form_context(
        "Add Product",
        form_data=request.POST if request.method == "POST" else None,
    )
    context["form"] = form
    return render(
        request, "product_form.html", context
    )

@login_required
def edit_product(request, pk):
    p = get_object_or_404(Product,pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, instance=p)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("products")
    else:
        form = ProductForm(instance=p)
    context = product_form_context(
        "Edit Product",
        p=p,
        form_data=request.POST if request.method == "POST" else None,
    )
    context["form"] = form
    return render(request, "product_form.html", context)

@login_required
@require_POST
def delete_product(request,pk):
    get_object_or_404(Product,pk=pk).delete()
    messages.success(request, "Product removed.")
    return redirect("products")

@login_required
def stock_in(request):
    return stock_change(request, "IN")

@login_required
def stock_out(request):
    return stock_change(request, "OUT")

def stock_change(request, kind):
    products = Product.objects.select_related("category").order_by("name")
    if request.method == "POST":
        form = StockTransactionForm(request.POST, kind=kind)
        if form.is_valid():
            product = form.cleaned_data["product"]
            quantity = form.cleaned_data["quantity"]
            if kind == "OUT" and quantity > product.quantity:
                form.add_error(
                    "quantity",
                    f"Only {product.quantity} units are currently in stock.",
                )
            else:
                product.quantity += quantity if kind == "IN" else -quantity
                product.save(update_fields=["quantity"])
                StockTransaction.objects.create(
                    product=product,
                    transaction_type=kind,
                    quantity=quantity,
                    note=form.cleaned_data["note"],
                )
                messages.success(request, "Stock updated.")
                return redirect("dashboard")
    else:
        form = StockTransactionForm(kind=kind)
    return render(
        request,
        "stock_form.html",
        {
            "products": products,
            "kind": kind,
            "form": form,
        },
    )
