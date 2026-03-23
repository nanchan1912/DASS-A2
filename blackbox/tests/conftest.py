"""Shared fixtures and helpers for QuickCart black-box API tests."""

from __future__ import annotations

import os
from decimal import Decimal

import pytest
import requests


BASE_URL = os.getenv("QUICKCART_BASE_URL", "http://127.0.0.1:8080/api/v1")
ROLL_NUMBER = os.getenv("QUICKCART_ROLL_NUMBER", "123456")


def _require_json(response: requests.Response):
    """Return parsed JSON and fail clearly when the response is not JSON."""
    content_type = response.headers.get("Content-Type", "")
    assert "application/json" in content_type.lower(), (
        f"Expected JSON response, got Content-Type={content_type!r} "
        f"and body={response.text[:300]!r}"
    )
    return response.json()


def _as_list(payload):
    """Extract a list payload from either a raw list or a wrapped dict."""
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "items", "results", "users", "products", "orders"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
    pytest.fail(f"Expected list-shaped JSON payload, got: {payload!r}")


def _as_object(payload):
    """Extract a dict payload from either a raw dict or a wrapped dict."""
    if isinstance(payload, dict):
        return payload
    pytest.fail(f"Expected object-shaped JSON payload, got: {payload!r}")


@pytest.fixture(scope="session")
def session() -> requests.Session:
    """Shared HTTP session."""
    return requests.Session()


@pytest.fixture(scope="session")
def admin_headers():
    """Headers for admin/data-inspection endpoints."""
    return {"X-Roll-Number": ROLL_NUMBER}


@pytest.fixture(scope="session", autouse=True)
def api_ready(session: requests.Session, admin_headers):
    """Skip the suite if the API is not reachable."""
    try:
        response = session.get(
            f"{BASE_URL}/admin/users",
            headers=admin_headers,
            timeout=10,
        )
    except requests.RequestException as exc:
        pytest.skip(f"QuickCart API is not reachable at {BASE_URL}: {exc}")
    assert response.status_code == 200, response.text


@pytest.fixture(scope="session")
def admin_users(session: requests.Session, admin_headers):
    """All users from the admin endpoint."""
    response = session.get(f"{BASE_URL}/admin/users", headers=admin_headers, timeout=15)
    payload = _require_json(response)
    users = _as_list(payload)
    assert users, "Expected at least one seeded user from /admin/users"
    return users


@pytest.fixture(scope="session")
def user_id(admin_users):
    """Reusable valid user id."""
    return admin_users[0]["user_id"]


@pytest.fixture
def user_headers(user_id):
    """Headers for user-scoped endpoints."""
    return {
        "X-Roll-Number": ROLL_NUMBER,
        "X-User-ID": str(user_id),
    }


@pytest.fixture(scope="session")
def admin_products(session: requests.Session, admin_headers):
    """All products including inactive ones."""
    response = session.get(
        f"{BASE_URL}/admin/products",
        headers=admin_headers,
        timeout=20,
    )
    payload = _require_json(response)
    products = _as_list(payload)
    assert products, "Expected seeded products from /admin/products"
    return products


@pytest.fixture(scope="session")
def active_product(admin_products):
    """An active product with stock, suitable for cart tests."""
    for product in admin_products:
        if product.get("is_active") and product.get("stock_quantity", 0) >= 5:
            return product
    pytest.fail("No active product with enough stock was found")


@pytest.fixture(scope="session")
def expired_coupon(session: requests.Session, admin_headers):
    """A coupon that is clearly expired in the seeded data."""
    response = session.get(
        f"{BASE_URL}/admin/coupons",
        headers=admin_headers,
        timeout=15,
    )
    payload = _require_json(response)
    coupons = _as_list(payload)
    for coupon in coupons:
        code = str(coupon.get("coupon_code", ""))
        if "EXPIRED" in code.upper():
            return coupon
    pytest.fail("No expired coupon found in seeded data")


def clear_cart(session: requests.Session, user_headers):
    """Best-effort cart cleanup for stateful tests."""
    response = session.delete(f"{BASE_URL}/cart/clear", headers=user_headers, timeout=15)
    assert response.status_code == 200, response.text


def get_cart(session: requests.Session, user_headers):
    """Get the current cart as JSON."""
    response = session.get(f"{BASE_URL}/cart", headers=user_headers, timeout=15)
    assert response.status_code == 200, response.text
    return _as_object(_require_json(response))


def decimal_value(value) -> Decimal:
    """Stable decimal conversion for money/rating checks."""
    return Decimal(str(value))
