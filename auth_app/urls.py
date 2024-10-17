from django.urls import path
from .views import *

urlpatterns = [
    path('signUpWithGoogle/', SignUpWithGoogleAuth.as_view(), name='signUpWithGoogle'),

]