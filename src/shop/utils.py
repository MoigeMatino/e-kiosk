from .models import User

def create_user_from_oidc(claims):
    """Create a user from OIDC claims"""
    email = claims.get("email")
    if not email:
        raise ValueError("OIDC response did not contain an email address.")

    # Check if the user already exists
    user = User.objects.filter(email=email).first()
    if user:
        return user
    
    # Create the user
    user = User.objects.create_user(
        email=email,
        password=None,  # Users won't have a password for OIDC login
        role=User.CUSTOMER,  # Default role; adjust as necessary
        openid_sub=claims.get("sub"),
    )
    user.save()
    return user
