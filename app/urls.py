from django.urls import path
from app.views import ImageProcessView, ImageDownloadView, DownloadFreePikView, FigmaLinkProcessAPI

urlpatterns = [
    path('uploadImage/', ImageProcessView.as_view(), name='ImageProcessView'),
    path('figmaLink/', FigmaLinkProcessAPI.as_view(), name='testImage'),
    path('downloadImage', ImageDownloadView.as_view(), name='download_image'),
    path('downloadFreePik', DownloadFreePikView.as_view(), name='download_fpk'),
]
