from rest_framework.test import APITestCase
from django.core.cache import cache

from users.models import User
from users.email_service import email_verification_service


class EmailAuthAndUserInfoTests(APITestCase):
    def setUp(self):
        self.register_send_url = "/api/users/auth/email/register/send-code/"
        self.register_verify_url = "/api/users/auth/email/register/verify-code/"
        self.login_send_url = "/api/users/auth/email/login/send-code/"
        self.login_verify_url = "/api/users/auth/email/login/verify-code/"
        self.me_url = "/api/users/me/"
        self.jwt_verify_url = "/api/users/auth/jwt/verify/"
        cache.clear()

    # --- Task 1: error when user exists (registration) ---
    def test_register_send_code_existing_user_returns_400(self):
        User.objects.create_user(email="exists@example.com", role="CLIENT")
        resp = self.client.post(
            self.register_send_url,
            {"email": "exists@example.com", "privacy_policy_accepted": True},
            format="json",
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data.get("error"), "Пользователь с таким email уже существует")

    def test_login_send_code_non_existing_user_returns_400(self):
        resp = self.client.post(self.login_send_url, {"email": "missing@example.com"}, format="json")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.data.get("error"), "Пользователь не найден")

    # --- Task 2: name field in user + returned in user info ---
    def test_register_verify_returns_name_field(self):
        email = "newuser@example.com"
        code = "1234"
        email_verification_service.save_code_to_cache(email, code, purpose="auth")

        resp = self.client.post(
            self.register_verify_url,
            {"email": email, "code": code, "device_id": "device-1", "privacy_policy_accepted": True},
            format="json",
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("user", resp.data)
        self.assertIn("name", resp.data["user"])  # поле есть (может быть null)

    def test_me_returns_name_field(self):
        # создаём пользователя и выдаём токен через login/verify
        email = "me@example.com"
        user = User.objects.create_user(email=email, role="CLIENT")
        user.name = "Vania"
        user.save(update_fields=["name"])

        code = "5678"
        email_verification_service.save_code_to_cache(email, code, purpose="auth")

        login_resp = self.client.post(
            self.login_verify_url,
            {"email": email, "code": code, "device_id": "device-me"},
            format="json",
        )
        self.assertEqual(login_resp.status_code, 200)
        access = login_resp.data["jwt"]["access"]

        # /me требует Bearer
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me_resp = self.client.get(self.me_url, format="json")
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.data.get("name"), "Vania")

    def test_jwt_verify_returns_name_field(self):
        email = "jwtname@example.com"
        user = User.objects.create_user(email=email, role="CLIENT")
        user.name = "Neo"
        user.save(update_fields=["name"])

        code = "9999"
        email_verification_service.save_code_to_cache(email, code, purpose="auth")

        login_resp = self.client.post(
            self.login_verify_url,
            {"email": email, "code": code, "device_id": "device-jwt"},
            format="json",
        )
        self.assertEqual(login_resp.status_code, 200)

        access = login_resp.data["jwt"]["access"]
        verify_resp = self.client.post(self.jwt_verify_url, {"token": access}, format="json")

        self.assertEqual(verify_resp.status_code, 200)
        self.assertTrue(verify_resp.data.get("valid"))
        self.assertEqual(verify_resp.data["user"].get("name"), "Neo")