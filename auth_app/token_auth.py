from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CustomTokenAuthentication(TokenAuthentication):
    keyword = 'Bearer'

    def authenticate_credentials(self, key):
        model = self.get_model()
        try:
            token = model.objects.select_related('user').get(key=key)
        except model.DoesNotExist:
            raise AuthenticationFailed({'detail': 'Invalid token or Expire.'})

        if not token.user.is_active:
            raise AuthenticationFailed({'detail': 'User inactive or deleted.'})

        return token.user, token
