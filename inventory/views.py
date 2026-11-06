from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from .models import Product, Category, StockTransaction


def product_form_context(title, p=None, form_data=None):
    categories = Category.objects.all()
    category_id = form_data.get("category") if form_data else (
        p.category_id if p else None
    )
    selected_category = categories.filter(pk=category_id).first() if category_id else None
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
        "stock_total": products.aggregate(x=Sum("quantity"))["x"] or 0,
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
        category_id = request.POST.get("category") or None
        category = Category.objects.filter(pk=category_id).first() if category_id else None
        is_playing_card = bool(category and category.name == "Playing Card")
        subcategory = request.POST.get("subcategory", "").strip()
        if is_playing_card and subcategory not in ("5G", "4G"):
            messages.error(request, "Choose a 5G or 4G subcategory for Playing Card.")
            return render(
                request,
                "product_form.html",
                product_form_context("Add Product", form_data=request.POST),
            )
        Product.objects.create(
            name=request.POST["name"], sku=request.POST["sku"],
            category=category,
            subcategory=subcategory if is_playing_card else "",
            purchase_price=request.POST.get("purchase_price") or 0,
            selling_price=request.POST.get("selling_price") or 0,
            quantity=request.POST.get("quantity") or 0,
            low_stock_limit=request.POST.get("low_stock_limit") or (
                2 if is_playing_card else 5
            ),
        )
        messages.success(request,"Product added successfully.")
        return redirect("products")
    return render(
        request, "product_form.html", product_form_context("Add Product")
    )

@login_required
def edit_product(request, pk):
    p = get_object_or_404(Product,pk=pk)
    if request.method == "POST":
        category_id = request.POST.get("category") or None
        category = Category.objects.filter(pk=category_id).first() if category_id else None
        is_playing_card = bool(category and category.name == "Playing Card")
        subcategory = request.POST.get("subcategory", "").strip()
        if is_playing_card and subcategory not in ("5G", "4G"):
            messages.error(request, "Choose a 5G or 4G subcategory for Playing Card.")
            return render(
                request,
                "product_form.html",
                product_form_context("Edit Product", p=p, form_data=request.POST),
            )
        p.name=request.POST["name"]; p.sku=request.POST["sku"]
        p.category=category
        p.subcategory=subcategory if is_playing_card else ""
        p.purchase_price=request.POST.get("purchase_price") or 0
        p.selling_price=request.POST.get("selling_price") or 0
        p.quantity=request.POST.get("quantity") or 0
        p.low_stock_limit=request.POST.get("low_stock_limit") or (
            2 if is_playing_card else 5
        )
        p.save()
        messages.success(request,"Product updated.")
        return redirect("products")
    return render(
        request, "product_form.html", product_form_context("Edit Product", p=p)
    )

@login_required
def delete_product(request,pk):
    get_object_or_404(Product,pk=pk).delete()
    return redirect("products")

@login_required
def stock_in(request):
    return stock_change(request, "IN")

@login_required
def stock_out(request):
    return stock_change(request, "OUT")

def stock_change(request, kind):
    if request.method == "POST":
        p=get_object_or_404(Product,pk=request.POST["product"])
        qty=int(request.POST["quantity"])
        if kind=="OUT" and qty>p.quantity:
            messages.error(request,"Not enough stock.")
        else:
            p.quantity += qty if kind=="IN" else -qty
            p.save()
            StockTransaction.objects.create(product=p,transaction_type=kind,quantity=qty,note=request.POST.get("note",""))
            messages.success(request,"Stock updated.")
        return redirect("dashboard")
    return render(request,"stock_form.html",{"products":Product.objects.all(),"kind":kind})
