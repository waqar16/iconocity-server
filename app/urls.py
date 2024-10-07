from django.urls import path
from app.views import (
    ImageProcessView,
    ImageDownloadView,
    DownloadFreePikView,
    FigmaLinkProcessAPI,
    GetProjectListApi,
    GetProjectIconListApi,
    ChangeProjectName,
    GetProjectHistoryListApi,
    GetHistoryByHistoryIdApi,
)

urlpatterns = [
    path('uploadImage/', ImageProcessView.as_view(), name='ImageProcessView'),
    path('figmaLink/', FigmaLinkProcessAPI.as_view(), name='testImage'),
    path('downloadImage', ImageDownloadView.as_view(), name='download_image'),
    path('downloadFreePik', DownloadFreePikView.as_view(), name='download_fpk'),
    path('getProjectList', GetProjectListApi.as_view(), name='get_project_list'),
    path('getProjectIconList/', GetProjectIconListApi.as_view(), name='get_project_icon'),
    path('changeProjectName/', ChangeProjectName.as_view(), name='change_project_name'),
    path('getProjectHistoryList/', GetProjectHistoryListApi.as_view(), name='get_project_history'),
    path('getHistoryByHistoryId/', GetHistoryByHistoryIdApi.as_view(), name='get_history_by_history_id'),

]
