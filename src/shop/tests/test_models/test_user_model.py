import pytest
from shop.models import User
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_phone_number_validation():
    """Test phone number validation for the User model."""
    # Case 1: Valid phone number
    user = User(
        email='validuser@example.com',
        openid_sub='1234567890',
        phone_number='+254711223344',
        role=User.CUSTOMER
    )
    try:
        user.clean()  # triggers validation
    except ValidationError:
        pytest.fail('Valid phone number should not raise a ValidationError.')

    # Case 2: phone number with dashes
    user.phone_number = '+254-712-345-678'  # Test with dashes
    try:
        user.clean()
        assert user.phone_number == '+254712345678'
    except ValidationError:
        pytest.fail('Valid phone number with dashes should not raise a ValidationError.')
        
    # Case 3: phone number with spaces
    user.phone_number = '+254 712 345 678'  # Test with dashes
    try:
        user.clean()
        assert user.phone_number == '+254712345678'
    except ValidationError:
        pytest.fail('Valid phone number with dashes should not raise a ValidationError.')
    
    # Case 4: Invalid phone number - string
    user.phone_number = 'invalid_phone'
    with pytest.raises(ValidationError) as excinfo:
        user.clean()

    assert 'phone_number' in excinfo.value.message_dict
    assert 'Invalid phone number format. Use: +254700123456' in excinfo.value.message_dict['phone_number'][0]
    
    # Case 5: Invalid phone number - missing +254
    user.phone_number = '0712345678'  # Invalid format (missing +254)
    with pytest.raises(ValidationError) as excinfo:
        user.clean()
    assert 'Invalid phone number format. Use: +254700123456' in excinfo.value.message_dict['phone_number'][0]

