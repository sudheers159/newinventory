from django.contrib import messages
from django.db.models import F, Sum
from django.shortcuts import get_object_or_404, redirect, render
from .models import Product, Category, StockTransaction

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

def products(request):
    q = request.GET.get("q","").strip()
    qs = Product.objects.select_related("category").all()
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(sku__icontains=q)
    return render(request, "products.html", {"products": qs, "q": q})

def add_product(request):
    if request.method == "POST":
        Product.objects.create(
            name=request.POST["name"], sku=request.POST["sku"],
            category_id=request.POST.get("category") or None,
            purchase_price=request.POST.get("purchase_price") or 0,
            selling_price=request.POST.get("selling_price") or 0,
            quantity=request.POST.get("quantity") or 0,
            low_stock_limit=request.POST.get("low_stock_limit") or 5,
        )
        messages.success(request,"Product added successfully.")
        return redirect("products")
    return render(request,"product_form.html",{"categories":Category.objects.all(),"title":"Add Product"})

def edit_product(request, pk):
    p = get_object_or_404(Product,pk=pk)
    if request.method == "POST":
        p.name=request.POST["name"]; p.sku=request.POST["sku"]
        p.category_id=request.POST.get("category") or None
        p.purchase_price=request.POST.get("purchase_price") or 0
        p.selling_price=request.POST.get("selling_price") or 0
        p.quantity=request.POST.get("quantity") or 0
        p.low_stock_limit=request.POST.get("low_stock_limit") or 5
        p.save()
        messages.success(request,"Product updated.")
        return redirect("products")
    return render(request,"product_form.html",{"categories":Category.objects.all(),"p":p,"title":"Edit Product"})

def delete_product(request,pk):
    get_object_or_404(Product,pk=pk).delete()
    return redirect("products")

def stock_in(request):
    return stock_change(request, "IN")

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
