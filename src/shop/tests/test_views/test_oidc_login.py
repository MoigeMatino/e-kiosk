from unittest.mock import PropertyMock, patch

import pytest
from django.http import HttpResponse

from shop.models import User


@pytest.mark.django_db
@patch("mozilla_django_oidc.views.OIDCAuthenticationCallbackView.get")
def test_first_time_login_redirects_to_update_profile(mock_get, client, oidc_callback_url):
    """Test that first-time login redirects to update_profile if phone_number is missing"""
    user = User.objects.create(email="testuser@example.com", openid_sub="1234567890", role=User.CUSTOMER)

    response_mock = HttpResponse("<h1>Update Profile</h1>", status=200)
    response_mock.user = user
    type(response_mock.user).is_authenticated = PropertyMock(return_value=True)
    mock_get.return_value = response_mock

    response = client.get(oidc_callback_url)
    assert response.status_code == 200
    assert "Update Profile" in response.content.decode()

    user = User.objects.get(email="testuser@example.com")
    assert user.phone_number is None
    assert user.role == User.CUSTOMER


@pytest.mark.django_db
@patch("mozilla_django_oidc.views.OIDCAuthenticationCallbackView.get")
def test_subsequent_login_no_redirect(mock_get, client, oidc_callback_url):
    """Test that subsequent login does not redirect to update_profile if phone_number exists"""
    user = User.objects.create(
        email="existinguser@example.com",
        openid_sub="0987654321",
        phone_number="123456789",
        role=User.CUSTOMER,
    )

    # Mock the OIDC response with a real HttpResponse object
    response_mock = HttpResponse()
    response_mock.user = user
    type(response_mock.user).is_authenticated = PropertyMock(return_value=True)
    mock_get.return_value = response_mock

    response = client.get(oidc_callback_url)
    assert response.status_code == 200
    assert "update_profile" not in response.content.decode()
    assert User.objects.filter(email="existinguser@example.com").count() == 1
