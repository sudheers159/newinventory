from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Category, Product, StockTransaction


class LoginFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="inventory-user",
            password="test-password-123",
        )

    def test_inventory_pages_redirect_anonymous_users_to_login(self):
        response = self.client.get("/")

        self.assertRedirects(response, "/login/?next=/")

    def test_login_and_logout(self):
        response = self.client.post(
            "/login/",
            {"username": self.user.username, "password": "test-password-123"},
        )

        self.assertRedirects(response, "/")
        self.assertEqual(self.client.get("/").status_code, 200)

        response = self.client.post("/logout/")

        self.assertRedirects(response, "/login/")
        self.assertRedirects(self.client.get("/"), "/login/?next=/")

    def test_login_page_reports_invalid_credentials(self):
        response = self.client.post(
            "/login/",
            {"username": self.user.username, "password": "incorrect"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Your username or password wasn’t recognized.")


class PlayingCardProductTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username="stock-manager",
            password="test-password-123",
        )
        self.client.force_login(user)
        self.playing_card, _ = Category.objects.get_or_create(name="Playing Card")
        self.device, _ = Category.objects.get_or_create(name="Device")
        self.camera, _ = Category.objects.get_or_create(name="Camera")

    def product_data(self, category, **extra):
        data = {
            "name": "Card Stock",
            "sku": "CARD-001",
            "category": str(category.pk),
            "quantity": "2",
        }
        data.update(extra)
        return data

    def test_playing_card_uses_subcategory_and_low_stock_warning(self):
        response = self.client.post(
            "/products/add/",
            self.product_data(self.playing_card, subcategory="5C"),
        )

        self.assertRedirects(response, "/products/")
        product = Product.objects.get(sku="CARD-001")
        self.assertEqual(product.subcategory, "5C")
        self.assertEqual(product.low_stock_limit, 2)
        self.assertTrue(product.is_low_stock)

        response = self.client.get("/products/")
        self.assertContains(response, "Playing Card · 5C")
        self.assertContains(response, 'class="stock-low"')
        self.assertContains(response, "Low · 2")

    def test_playing_card_requires_a_subcategory(self):
        response = self.client.post(
            "/products/add/",
            self.product_data(self.playing_card),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose a subcategory for Playing Card.")

    def test_playing_card_accepts_5b_and_4g(self):
        for subcategory, sku in (("5B", "CARD-5B"), ("4G", "CARD-4G")):
            response = self.client.post(
                "/products/add/",
                self.product_data(
                    self.playing_card,
                    subcategory=subcategory,
                    sku=sku,
                    name=f"Card Stock {subcategory}",
                ),
            )
            self.assertRedirects(response, "/products/")
            self.assertEqual(
                Product.objects.get(sku=sku).subcategory,
                subcategory,
            )

    def test_other_categories_do_not_keep_playing_card_subcategory(self):
        response = self.client.post(
            "/products/add/",
            self.product_data(self.device, subcategory="5C"),
        )

        self.assertRedirects(response, "/products/")
        product = Product.objects.get(sku="CARD-001")
        self.assertEqual(product.subcategory, "")
        self.assertEqual(product.low_stock_limit, 5)

    def test_same_dealer_details_can_be_used_across_categories(self):
        Product.objects.create(
            name="Existing",
            sku="CARD-001",
            category=self.device,
        )

        response = self.client.post(
            "/products/add/",
            self.product_data(self.camera, name="Camera item"),
        )
        self.assertRedirects(response, "/products/")
        response = self.client.post(
            "/products/add/",
            self.product_data(
                self.playing_card,
                subcategory="5C",
                name="Card item",
            ),
        )
        self.assertRedirects(response, "/products/")
        self.assertEqual(
            Product.objects.filter(sku="CARD-001").count(),
            3,
        )

    def test_duplicate_dealer_details_can_be_used_in_same_category(self):
        Product.objects.create(
            name="Existing",
            sku="CARD-001",
            category=self.device,
        )

        response = self.client.post("/products/add/", self.product_data(self.device))

        self.assertRedirects(response, "/products/")
        self.assertEqual(Product.objects.filter(sku="CARD-001").count(), 2)

    def test_product_name_can_be_reused_across_categories(self):
        Product.objects.create(
            name="Card Stock",
            sku="EXISTING-001",
            category=self.device,
        )

        response = self.client.post("/products/add/", self.product_data(self.camera))

        self.assertRedirects(response, "/products/")
        self.assertEqual(
            Product.objects.filter(name="Card Stock").count(),
            2,
        )

    def test_same_name_cannot_be_reused_for_same_category_and_subcategory(self):
        first_response = self.client.post(
            "/products/add/",
            self.product_data(
                self.playing_card,
                subcategory="5C",
                sku="CARD-5C",
            ),
        )
        second_response = self.client.post(
            "/products/add/",
            self.product_data(
                self.playing_card,
                subcategory="5C",
                sku="CARD-5C-DUPLICATE",
            ),
        )

        self.assertRedirects(first_response, "/products/")
        self.assertEqual(second_response.status_code, 200)
        self.assertContains(
            second_response,
            "A product with this name already exists in this category and subcategory.",
        )
        self.assertEqual(
            Product.objects.filter(name="Card Stock", category=self.playing_card).count(),
            1,
        )

    def test_same_playing_card_name_can_be_reused_for_another_subcategory(self):
        first_response = self.client.post(
            "/products/add/",
            self.product_data(
                self.playing_card,
                subcategory="5C",
                sku="CARD-5C",
            ),
        )
        second_response = self.client.post(
            "/products/add/",
            self.product_data(
                self.playing_card,
                subcategory="4G",
                sku="CARD-4G",
            ),
        )

        self.assertRedirects(first_response, "/products/")
        self.assertRedirects(second_response, "/products/")
        self.assertEqual(
            Product.objects.filter(name="Card Stock", category=self.playing_card).count(),
            2,
        )

    def test_playing_card_subcategory_can_be_reused_for_a_different_product_name(self):
        Product.objects.create(
            name="Existing card",
            sku="CARD-EXISTING",
            category=self.playing_card,
            subcategory="5C",
        )

        response = self.client.post(
            "/products/add/",
            self.product_data(
                self.playing_card,
                name="Another card",
                sku="CARD-ANOTHER",
                subcategory="5C",
            ),
        )

        self.assertRedirects(response, "/products/")
        self.assertEqual(
            Product.objects.filter(
                category=self.playing_card,
                subcategory="5C",
            ).count(),
            2,
        )

    def test_product_removal_requires_post_and_succeeds(self):
        product = Product.objects.create(
            name="To remove",
            sku="REMOVE-001",
            category=self.device,
        )

        response = self.client.get(f"/products/{product.pk}/delete/")
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Product.objects.filter(pk=product.pk).exists())

        response = self.client.post(f"/products/{product.pk}/delete/")
        self.assertRedirects(response, "/products/")
        self.assertFalse(Product.objects.filter(pk=product.pk).exists())

    def test_product_export_formats_download_with_data(self):
        Product.objects.create(
            name="Export item",
            sku="EXPORT-001",
            category=self.device,
            quantity=3,
        )

        csv_response = self.client.get("/products/export/csv/")
        self.assertEqual(csv_response.status_code, 200)
        self.assertEqual(csv_response["Content-Type"], "text/csv")
        self.assertContains(csv_response, "Export item")
        self.assertIn(".csv", csv_response["Content-Disposition"])

        excel_response = self.client.get("/products/export/excel/")
        self.assertEqual(excel_response.status_code, 200)
        self.assertEqual(
            excel_response["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertIn(".xlsx", excel_response["Content-Disposition"])

        pdf_response = self.client.get("/products/export/pdf/")
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertIn(".pdf", pdf_response["Content-Disposition"])

    def test_dashboard_shows_stock_in_and_out_unit_totals(self):
        product = Product.objects.create(
            name="Dashboard item",
            sku="DASH-001",
            category=self.device,
            quantity=8,
        )
        StockTransaction.objects.create(
            product=product,
            transaction_type=StockTransaction.IN,
            quantity=12,
        )
        StockTransaction.objects.create(
            product=product,
            transaction_type=StockTransaction.OUT,
            quantity=4,
        )

        response = self.client.get("/")

        self.assertContains(response, "Products In Stock")
        self.assertContains(response, "Products Sold")
        self.assertContains(response, "Stock In (units)")
        self.assertContains(response, "Sales / Stock Out (units)")
        self.assertEqual(response.context["products_in_stock"], 1)
        self.assertEqual(response.context["products_sold"], 1)
        self.assertEqual(response.context["stock_total"], 8)
        self.assertEqual(response.context["stock_in_total"], 12)
        self.assertEqual(response.context["stock_out_total"], 4)

    def test_stock_in_page_lists_all_products_and_adds_quantity(self):
        stocked = Product.objects.create(
            name="Available item",
            sku="AVAILABLE-001",
            category=self.device,
            quantity=5,
        )
        out_of_stock = Product.objects.create(
            name="Empty item",
            sku="EMPTY-001",
            category=self.device,
            quantity=0,
        )

        response = self.client.get("/stock-in/")

        self.assertContains(response, "All Products and Current Stock")
        self.assertContains(response, "Available item")
        self.assertContains(response, "Empty item")
        self.assertContains(response, ">5</td>")
        self.assertContains(response, ">0</td>")

        response = self.client.post(
            "/stock-in/",
            {"product": stocked.pk, "quantity": 3},
        )

        self.assertRedirects(response, "/")
        stocked.refresh_from_db()
        out_of_stock.refresh_from_db()
        self.assertEqual(stocked.quantity, 8)
        self.assertEqual(out_of_stock.quantity, 0)
        self.assertTrue(
            StockTransaction.objects.filter(
                product=stocked,
                transaction_type=StockTransaction.IN,
                quantity=3,
            ).exists()
        )

    def test_stock_out_page_lists_inventory_and_records_available_sales(self):
        available = Product.objects.create(
            name="Available sale",
            sku="SALE-001",
            category=self.device,
            quantity=5,
        )
        empty = Product.objects.create(
            name="Unavailable sale",
            sku="SALE-002",
            category=self.device,
            quantity=0,
        )

        response = self.client.get("/stock-out/")

        self.assertContains(response, "All Products and Current Stock")
        self.assertContains(response, "Available sale")
        self.assertContains(response, "Unavailable sale")
        self.assertEqual(
            list(response.context["form"].fields["product"].queryset),
            [available],
        )

        response = self.client.post(
            "/stock-out/",
            {"product": available.pk, "quantity": 2},
        )

        self.assertRedirects(response, "/")
        available.refresh_from_db()
        empty.refresh_from_db()
        self.assertEqual(available.quantity, 3)
        self.assertEqual(empty.quantity, 0)
        self.assertTrue(
            StockTransaction.objects.filter(
                product=available,
                transaction_type=StockTransaction.OUT,
                quantity=2,
            ).exists()
        )

    def test_stock_out_rejects_sales_above_available_quantity(self):
        product = Product.objects.create(
            name="Limited stock",
            sku="LIMITED-001",
            category=self.device,
            quantity=2,
        )

        response = self.client.post(
            "/stock-out/",
            {"product": product.pk, "quantity": 3},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only 2 units are currently in stock.")
        product.refresh_from_db()
        self.assertEqual(product.quantity, 2)
        self.assertFalse(StockTransaction.objects.filter(product=product).exists())
