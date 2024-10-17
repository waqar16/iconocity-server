from django.db import transaction
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.models import User


class SignUpWithGoogleAuth(APIView):   # Both purpose for Sign In and Sign Up
    permission_classes = [AllowAny, ]

    def post(self, request, *args, **kwargs):
        with transaction.atomic():
            email = request.data.get('email')
            full_name = request.data.get('full_name')
            profile_image = request.data.get('profile_image')

            try:
                user = User.objects.get(email=email)
                auth_token = Token.objects.get(user=user)

            except User.DoesNotExist:
                user = User.objects.create_user(email=email, full_name=full_name, profile_image=profile_image,
                                                         username=email.split('@')[0], password='someNot@dmin',
                                                         is_active=True)
                if user:
                    auth_token = Token.objects.create(user=user)

            if auth_token:
                user.is_active = True
                user.save()
                return Response({'success': 'signup successfully', 'email': user.email, 'token': auth_token.key,
                    'profile_image': profile_image}, status=status.HTTP_200_OK)