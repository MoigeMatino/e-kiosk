import pytest
from shop.models import User

@pytest.mark.django_db
def test_update_profile_success(client, update_profile_url):
    """Test successful profile update with valid data"""
    user = User.objects.create(
        email='testuser@example.com',
        openid_sub='1234567890',
        phone_number='',
        role=User.CUSTOMER
    )
    # Log in the user
    client.force_login(user)
    
    data = {
        'phone_number': '123456789',
        
    }
    response = client.patch(update_profile_url, data, content_type='application/json')

    user.refresh_from_db()
    assert response.status_code == 200
    assert response.json() == {'message': 'Profile updated successfully.'}
    assert user.phone_number == '123456789'
    assert user.openid_sub == '1234567890'
    assert user.role == User.CUSTOMER


@pytest.mark.django_db
def test_update_profile_validation_error(client, update_profile_url):
    """Test profile update fails with invalid data"""
    user = User.objects.create(
        email="testuser@example.com",
        openid_sub="1234567890",
        role=User.CUSTOMER
    )
    # Log in the user
    client.force_login(user)    
    
    data = {
        'phone_number': '',  # Missing phone number
    }
    response = client.patch(update_profile_url, data, content_type='application/json')

    user.refresh_from_db()
    assert response.status_code == 400
    assert response.json() == {'error': 'Phone number is required.'}
    assert user.phone_number is None


@pytest.mark.django_db
def test_update_profile_unauthorized(client, update_profile_url):
    """Test that an unauthenticated user cannot access the update profile endpoint"""
    
    data = {
        'email':'testuser@example.com',
        'role': User.CUSTOMER
    }
    response = client.patch(update_profile_url, data, content_type='application/json')

    assert response.status_code == 403   
