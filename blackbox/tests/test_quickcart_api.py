"""Black-box tests for the QuickCart REST API."""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

import pytest

from conftest import BASE_URL, _as_list, _as_object, _require_json, clear_cart, decimal_value, get_cart


class TestHeadersAndAdmin:
    """Header validation and admin inspection endpoints."""

    @pytest.mark.parametrize(
        ("path", "expected_key"),
        [
            ("/admin/users", "user_id"),
            ("/admin/products", "product_id"),
            ("/admin/orders", "order_id"),
            ("/admin/carts", "cart_id"),
            ("/admin/coupons", "coupon_code"),
            ("/admin/tickets", "ticket_id"),
            ("/admin/addresses", "address_id"),
        ],
    )
    def test_admin_endpoint_returns_json_list(
        self,
        session,
        admin_headers,
        path,
        expected_key,
    ):
        response = session.get(f"{BASE_URL}{path}", headers=admin_headers, timeout=20)
        assert response.status_code == 200, response.text
        payload = _require_json(response)
        items = _as_list(payload)
        assert isinstance(items, list)
        if items:
            assert expected_key in items[0]

    def test_missing_roll_header_returns_401(self, session):
        response = session.get(f"{BASE_URL}/admin/users", timeout=10)
        assert response.status_code == 401
        assert "X-Roll-Number" in response.text

    def test_invalid_roll_header_returns_400(self, session):
        response = session.get(
            f"{BASE_URL}/admin/users",
            headers={"X-Roll-Number": "abc"},
            timeout=10,
        )
        assert response.status_code == 400

    def test_missing_user_header_returns_400(self, session, admin_headers):
        response = session.get(f"{BASE_URL}/profile", headers=admin_headers, timeout=10)
        assert response.status_code == 400

    def test_invalid_user_header_returns_400(self, session, admin_headers):
        headers = dict(admin_headers)
        headers["X-User-ID"] = "not-a-number"
        response = session.get(f"{BASE_URL}/profile", headers=headers, timeout=10)
        assert response.status_code == 400


class TestProfileAndProducts:
    """Read and validation tests for profile and product APIs."""

    def test_profile_get_returns_expected_fields(self, session, user_headers):
        response = session.get(f"{BASE_URL}/profile", headers=user_headers, timeout=10)
        assert response.status_code == 200, response.text
        payload = _as_object(_require_json(response))
        for key in ("user_id", "name", "email", "phone", "wallet_balance", "loyalty_points"):
            assert key in payload

    def test_profile_put_rejects_short_name(self, session, user_headers):
        response = session.put(
            f"{BASE_URL}/profile",
            headers=user_headers,
            json={"name": "A", "phone": "1234567890"},
            timeout=10,
        )
        assert response.status_code == 400

    def test_profile_put_rejects_missing_phone(self, session, user_headers):
        response = session.put(
            f"{BASE_URL}/profile",
            headers=user_headers,
            json={"name": "Valid Name"},
            timeout=10,
        )
        assert response.status_code == 400

    def test_profile_put_rejects_invalid_phone_length(self, session, user_headers):
        response = session.put(
            f"{BASE_URL}/profile",
            headers=user_headers,
            json={"name": "Valid Name", "phone": "12345"},
            timeout=10,
        )
        assert response.status_code == 400

    def test_products_list_excludes_inactive_products(
        self,
        session,
        user_headers,
        admin_products,
    ):
        response = session.get(f"{BASE_URL}/products", headers=user_headers, timeout=20)
        assert response.status_code == 200, response.text
        user_products = _as_list(_require_json(response))
        inactive_ids = {
            product["product_id"]
            for product in admin_products
            if not product.get("is_active", False)
        }
        returned_ids = {product["product_id"] for product in user_products}
        assert returned_ids.isdisjoint(inactive_ids)

    def test_product_lookup_missing_id_returns_404(self, session, user_headers):
        response = session.get(f"{BASE_URL}/products/999999", headers=user_headers, timeout=10)
        assert response.status_code == 404

    def test_products_search_returns_matching_names(self, session, user_headers):
        response = session.get(
            f"{BASE_URL}/products",
            headers=user_headers,
            params={"search": "Apple"},
            timeout=15,
        )
        assert response.status_code == 200, response.text
        products = _as_list(_require_json(response))
        assert products, "Expected search to return at least one product"
        assert all("apple" in product["name"].lower() for product in products)

    def test_products_sort_ascending_by_price(self, session, user_headers):
        response = session.get(
            f"{BASE_URL}/products",
            headers=user_headers,
            params={"sort": "price_asc"},
            timeout=20,
        )
        assert response.status_code == 200, response.text
        products = _as_list(_require_json(response))
        prices = [product["price"] for product in products[:25]]
        assert prices == sorted(prices)

    def test_products_sort_descending_by_price(self, session, user_headers):
        response = session.get(
            f"{BASE_URL}/products",
            headers=user_headers,
            params={"sort": "price_desc"},
            timeout=20,
        )
        assert response.status_code == 200, response.text
        products = _as_list(_require_json(response))
        prices = [product["price"] for product in products[:25]]
        assert prices == sorted(prices, reverse=True)


class TestAddresses:
    """Address creation and validation tests."""

    def test_address_post_rejects_invalid_label(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/addresses",
            headers=user_headers,
            json={
                "label": "TEMP",
                "street": "12345 Test Street",
                "city": "Delhi",
                "pincode": "110011",
                "is_default": False,
            },
            timeout=15,
        )
        assert response.status_code == 400

    def test_address_post_rejects_missing_street(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/addresses",
            headers=user_headers,
            json={
                "label": "HOME",
                "city": "Delhi",
                "pincode": "110011",
                "is_default": False,
            },
            timeout=15,
        )
        assert response.status_code == 400

    def test_address_post_accepts_valid_six_digit_pincode(self, session, user_headers):
        unique = uuid4().hex[:8]
        response = session.post(
            f"{BASE_URL}/addresses",
            headers=user_headers,
            json={
                "label": "OTHER",
                "street": f"12345 Test Street {unique}",
                "city": "Delhi",
                "pincode": "110011",
                "is_default": False,
            },
            timeout=15,
        )
        assert response.status_code == 200, response.text
        payload = _as_object(_require_json(response))
        address = payload.get("address", payload)
        for key in ("address_id", "label", "street", "city", "pincode", "is_default"):
            assert key in address


class TestCartAndCoupons:
    """Cart math, validation, and coupon behavior."""

    def test_cart_add_rejects_zero_quantity(self, session, user_headers, active_product):
        clear_cart(session, user_headers)
        response = session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": active_product["product_id"], "quantity": 0},
            timeout=15,
        )
        assert response.status_code == 400

    def test_cart_add_rejects_string_quantity(self, session, user_headers, active_product):
        clear_cart(session, user_headers)
        response = session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": active_product["product_id"], "quantity": "two"},
            timeout=15,
        )
        assert response.status_code == 400

    def test_cart_add_missing_product_returns_404(self, session, user_headers):
        clear_cart(session, user_headers)
        response = session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": 999999, "quantity": 1},
            timeout=15,
        )
        assert response.status_code == 404

    def test_cart_accumulates_quantity_for_repeated_adds(self, session, user_headers, active_product):
        clear_cart(session, user_headers)
        product_id = active_product["product_id"]
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": product_id, "quantity": 1},
            timeout=15,
        )
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": product_id, "quantity": 1},
            timeout=15,
        )
        cart = get_cart(session, user_headers)
        item = next(item for item in cart["items"] if item["product_id"] == product_id)
        assert item["quantity"] == 2

    def test_cart_item_subtotal_equals_quantity_times_unit_price(
        self,
        session,
        user_headers,
        active_product,
    ):
        clear_cart(session, user_headers)
        product_id = active_product["product_id"]
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": product_id, "quantity": 1},
            timeout=15,
        )
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": product_id, "quantity": 1},
            timeout=15,
        )
        cart = get_cart(session, user_headers)
        item = next(item for item in cart["items"] if item["product_id"] == product_id)
        expected = decimal_value(item["quantity"]) * decimal_value(item["unit_price"])
        assert decimal_value(item["subtotal"]) == expected

    def test_cart_total_equals_sum_of_all_item_subtotals(
        self,
        session,
        user_headers,
        active_product,
        admin_products,
    ):
        clear_cart(session, user_headers)
        second_product = next(
            product
            for product in admin_products
            if product["product_id"] != active_product["product_id"]
            and product.get("is_active")
            and product.get("stock_quantity", 0) >= 1
        )
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": active_product["product_id"], "quantity": 1},
            timeout=15,
        )
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": second_product["product_id"], "quantity": 1},
            timeout=15,
        )
        cart = get_cart(session, user_headers)
        subtotal_sum = sum(decimal_value(item["subtotal"]) for item in cart["items"])
        assert decimal_value(cart["total"]) == subtotal_sum

    def test_coupon_apply_rejects_expired_coupon(
        self,
        session,
        user_headers,
        active_product,
        expired_coupon,
    ):
        clear_cart(session, user_headers)
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": active_product["product_id"], "quantity": 5},
            timeout=15,
        )
        response = session.post(
            f"{BASE_URL}/coupon/apply",
            headers=user_headers,
            json={"coupon_code": expired_coupon["coupon_code"]},
            timeout=15,
        )
        assert response.status_code == 400


class TestWalletLoyaltyAndCheckout:
    """Wallet, loyalty, and checkout validation tests."""

    def test_wallet_add_rejects_wrong_type(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/wallet/add",
            headers=user_headers,
            json={"amount": "ten"},
            timeout=15,
        )
        assert response.status_code == 400

    def test_wallet_add_rejects_above_limit(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/wallet/add",
            headers=user_headers,
            json={"amount": 100001},
            timeout=15,
        )
        assert response.status_code == 400

    def test_wallet_pay_deducts_exact_amount(self, session, user_headers):
        before = _as_object(
            _require_json(
                session.get(f"{BASE_URL}/wallet", headers=user_headers, timeout=15),
            ),
        )["wallet_balance"]
        response = session.post(
            f"{BASE_URL}/wallet/pay",
            headers=user_headers,
            json={"amount": 1},
            timeout=15,
        )
        assert response.status_code == 200, response.text
        after = _as_object(
            _require_json(
                session.get(f"{BASE_URL}/wallet", headers=user_headers, timeout=15),
            ),
        )["wallet_balance"]
        assert decimal_value(before) - decimal_value(after) == Decimal("1")

    def test_loyalty_redeem_rejects_zero_points(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/loyalty/redeem",
            headers=user_headers,
            json={"points": 0},
            timeout=15,
        )
        assert response.status_code == 400

    def test_checkout_rejects_invalid_payment_method(self, session, user_headers, active_product):
        clear_cart(session, user_headers)
        session.post(
            f"{BASE_URL}/cart/add",
            headers=user_headers,
            json={"product_id": active_product["product_id"], "quantity": 1},
            timeout=15,
        )
        response = session.post(
            f"{BASE_URL}/checkout",
            headers=user_headers,
            json={"payment_method": "UPI"},
            timeout=15,
        )
        assert response.status_code == 400

    def test_checkout_rejects_empty_cart(self, session, user_headers):
        clear_cart(session, user_headers)
        response = session.post(
            f"{BASE_URL}/checkout",
            headers=user_headers,
            json={"payment_method": "COD"},
            timeout=15,
        )
        assert response.status_code == 400


class TestOrdersReviewsAndSupport:
    """Order, review, and support-ticket tests."""

    def test_orders_detail_returns_404_for_missing_order(self, session, user_headers):
        response = session.get(f"{BASE_URL}/orders/999999", headers=user_headers, timeout=15)
        assert response.status_code == 404

    def test_orders_cancel_missing_order_returns_404(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/orders/999999/cancel",
            headers=user_headers,
            timeout=15,
        )
        assert response.status_code == 404

    def test_review_rejects_out_of_range_rating(self, session, user_headers, active_product):
        response = session.post(
            f"{BASE_URL}/products/{active_product['product_id']}/reviews",
            headers=user_headers,
            json={"rating": 6, "comment": "Too high"},
            timeout=15,
        )
        assert response.status_code == 400

    def test_review_average_is_decimal_after_new_review(self, session, user_headers, active_product):
        product_id = active_product["product_id"]
        before_response = session.get(
            f"{BASE_URL}/products/{product_id}/reviews",
            headers=user_headers,
            timeout=15,
        )
        assert before_response.status_code == 200, before_response.text
        before_payload = _as_object(_require_json(before_response))
        before_reviews = before_payload.get("reviews", [])
        before_sum = sum(decimal_value(review["rating"]) for review in before_reviews)
        before_count = len(before_reviews)

        post_response = session.post(
            f"{BASE_URL}/products/{product_id}/reviews",
            headers=user_headers,
            json={"rating": 5, "comment": f"blackbox-{uuid4().hex[:8]}"},
            timeout=15,
        )
        assert post_response.status_code == 200, post_response.text

        after_response = session.get(
            f"{BASE_URL}/products/{product_id}/reviews",
            headers=user_headers,
            timeout=15,
        )
        assert after_response.status_code == 200, after_response.text
        after_payload = _as_object(_require_json(after_response))
        expected_average = (before_sum + Decimal("5")) / Decimal(before_count + 1)
        assert decimal_value(after_payload["average_rating"]) == expected_average

    def test_support_ticket_rejects_short_subject(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/support/ticket",
            headers=user_headers,
            json={"subject": "Hey", "message": "Message body"},
            timeout=15,
        )
        assert response.status_code == 400

    def test_support_ticket_missing_message_returns_400(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/support/ticket",
            headers=user_headers,
            json={"subject": "Proper subject"},
            timeout=15,
        )
        assert response.status_code == 400

    def test_support_ticket_starts_open(self, session, user_headers):
        response = session.post(
            f"{BASE_URL}/support/ticket",
            headers=user_headers,
            json={
                "subject": f"Need help {uuid4().hex[:6]}",
                "message": "Testing support ticket creation",
            },
            timeout=15,
        )
        assert response.status_code == 200, response.text
        payload = _as_object(_require_json(response))
        assert payload["status"] == "OPEN"

    def test_support_ticket_disallows_backward_status_transition(self, session, user_headers):
        create_response = session.post(
            f"{BASE_URL}/support/ticket",
            headers=user_headers,
            json={
                "subject": f"Workflow {uuid4().hex[:6]}",
                "message": "Testing status workflow",
            },
            timeout=15,
        )
        assert create_response.status_code == 200, create_response.text
        created = _as_object(_require_json(create_response))
        ticket_id = created["ticket_id"]

        first_update = session.put(
            f"{BASE_URL}/support/tickets/{ticket_id}",
            headers=user_headers,
            json={"status": "IN_PROGRESS"},
            timeout=15,
        )
        assert first_update.status_code == 200, first_update.text

        backward_update = session.put(
            f"{BASE_URL}/support/tickets/{ticket_id}",
            headers=user_headers,
            json={"status": "OPEN"},
            timeout=15,
        )
        assert backward_update.status_code == 400
