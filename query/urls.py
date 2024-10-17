from django.urls import path
from query.views import *

urlpatterns = [
    path('UpdateIconsByQuery/', UpdateIconAttributesByQuery.as_view(), name='UpdateIconsByQuery'),
]
