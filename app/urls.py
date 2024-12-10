from django.urls import path
from app.views import (
    ImageProcessView,
    ImageDownloadView,
    DownloadFreePikView,
    FigmaLinkProcessAPI,
    ImageLinkProcessAPI,
    GetProjectListApi,
    GetProjectIconListApi,
    ChangeProjectName,
    GetProjectHistoryListApi,
    GetHistoryByHistoryIdApi,
    SimilarIconSearchAPI,
    DownloadIconsZip,
    GenerateIconVariationsAPIView,
    ExchangeFigmaCodeForTokenView
)

urlpatterns = [
    path('uploadImage/', ImageProcessView.as_view(), name='ImageProcessView'),
    path('figmaLink/', FigmaLinkProcessAPI.as_view(), name='testImage'),
    path('imageLink/', ImageLinkProcessAPI.as_view(), name='testImage'),
    path('similarIconSearch/', SimilarIconSearchAPI.as_view(), name='similar_icon_search'),
    path('downloadImage', ImageDownloadView.as_view(), name='download_image'),
    path('downloadFreePik', DownloadFreePikView.as_view(), name='download_fpk'),
    path('downloadIcons', DownloadIconsZip.as_view(), name='download_icons'),
    path('getProjectList', GetProjectListApi.as_view(), name='get_project_list'),
    path('getProjectIconList/', GetProjectIconListApi.as_view(), name='get_project_icon'),
    path('changeProjectName/', ChangeProjectName.as_view(), name='change_project_name'),
    path('getProjectHistoryList/', GetProjectHistoryListApi.as_view(), name='get_project_history'),
    path('getHistoryByHistoryId/', GetHistoryByHistoryIdApi.as_view(), name='get_history_by_history_id'),
    path('generateIconVariations/', GenerateIconVariationsAPIView.as_view(), name='generate_icon_variations'),
    path('exchangeFigmaCodeForToken/', ExchangeFigmaCodeForTokenView.as_view(), name='exchange_figma_code_for_token'),

]
