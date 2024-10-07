from django.urls import path
from query.views import (
    UpdateIconAttribuesByQuery,
)

urlpatterns = [
    path('UpdateIconsByQuery/', UpdateIconAttribuesByQuery.as_view(), name='UpdateIconsByQuery'),
]
