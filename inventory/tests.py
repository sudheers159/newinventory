from django.contrib.auth import get_user_model
from django.test import TestCase
from .models import Category, Product


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
            self.product_data(self.playing_card, subcategory="5G"),
        )

        self.assertRedirects(response, "/products/")
        product = Product.objects.get(sku="CARD-001")
        self.assertEqual(product.subcategory, "5G")
        self.assertEqual(product.low_stock_limit, 2)
        self.assertTrue(product.is_low_stock)

        response = self.client.get("/products/")
        self.assertContains(response, "Playing Card · 5G")
        self.assertContains(response, 'class="stock-low"')
        self.assertContains(response, "Low · 2")

    def test_playing_card_requires_a_subcategory(self):
        response = self.client.post(
            "/products/add/",
            self.product_data(self.playing_card),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose a 5G or 4G subcategory")

    def test_other_categories_do_not_keep_playing_card_subcategory(self):
        response = self.client.post(
            "/products/add/",
            self.product_data(self.device, subcategory="5G"),
        )

        self.assertRedirects(response, "/products/")
        product = Product.objects.get(sku="CARD-001")
        self.assertEqual(product.subcategory, "")
        self.assertEqual(product.low_stock_limit, 5)
