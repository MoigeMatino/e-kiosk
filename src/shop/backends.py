from mozilla_django_oidc.auth import OIDCAuthenticationBackend


class CustomOIDCBackend(OIDCAuthenticationBackend):
    def create_user(self, claims):
        """
        Custom logic to create a user
        invoked only once when the user logs in for the first time
        """
        email = claims.get("email")
        phone_number = claims.get("phone_number", "")
        role = claims.get("role", "customer")
        openid_sub = claims.get("sub", "")

        # Create user with the correct email and other fields
        user = self.UserModel.objects.create_user(
            email=email,
            phone_number=phone_number,
            role=role,
            openid_sub=openid_sub,
        )

        user.save()
        return user

    def update_user(self, user, claims):
        """
        logic that handles an existing user's subsequent logins
        used to sync user's information
        """
        user.email = claims.get("email", user.email)
        user.phone_number = claims.get("phone_number", user.phone_number)
        user.save()
        return user
