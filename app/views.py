import base64
import requests
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings
from langchain_openai import ChatOpenAI
from app.utils import process_image_data, custom_error_message, Color_Available_in_Filter
from app.serializers import ProjectSerializer, ProjectListSerializer, ProjectIconListSerializer
import re
import requests
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from app.models import Project
OPENAI_API_KEY = settings.OPENAI_API_KEY
ICON_FINDER_KEY = settings.ICON_FINDER_KEY
FIGMA_KEY = settings.FIGMA_API_KEY
fast_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o-mini", streaming=True)
import webcolors

class ImageProcessView(APIView):

    def post(self, request, *args, **kwargs):
        try:
            image_file = request.FILES.get('image')
            icon_color = request.data.get('icon_color')
            icon_style = request.data.get('icon_style')

            if not image_file:
                return Response({"error": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)

            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            result = process_image_data(image_base64)

            color_palette = result.get("color_palette", "")
            iconography = result.get("iconography", "")
            brand_style = result.get("brand_style", "")
            gradient_usage = result.get("gradient_usage", "")
            imagery = result.get("imagery", "")
            shadow_and_depth = result.get("shadow_and_depth", "")
            line_thickness = result.get("line_thickness", "")
            corner_rounding = result.get("corner_rounding", "")

            f_query = f"{icon_color} {icon_style} {color_palette} {iconography} {brand_style} {gradient_usage} {imagery} {shadow_and_depth} {line_thickness} {corner_rounding}"
            query = f"{iconography}"

            # Iconfinder API request
            url = f"https://api.iconfinder.com/v4/icons/search?query={query}&count=10"
            headers = {
                "accept": "application/json",
                "Authorization": f"Bearer {ICON_FINDER_KEY}"
            }

            response = requests.get(url, headers=headers)
            json_data = response.json()

            # Freepik API request
            f_url = "https://api.freepik.com/v1/icons"
            querystring = {"term": f_query, "thumbnail_size": "24", "per_page": "10",
                           "page": "1", }
            f_headers = {
                "x-freepik-api-key": "FPSX19dd1bf8e6534123a705ed38678cb8d1"}

            f_response = requests.get(f_url, headers=f_headers, params=querystring)
            f_json_data = f_response.json()

            icon_data_list = []
            for icon in json_data.get('icons', []):
                if not icon['is_premium']:
                    for raster_size in icon['raster_sizes']:
                        if raster_size['size'] == 20:  # Check if the size is 20
                            for format_info in raster_size['formats']:
                                icon_data = {
                                    'preview_url': format_info['preview_url'],
                                    'download_url': format_info['download_url']
                                }
                                icon_data_list.append(icon_data)

            # Extract Freepik icon data
            f_icons_list = []
            for icon in f_json_data.get('data', []):
                if icon.get('thumbnails'):
                    f_icons_list.append({
                        'id': icon.get('id'),
                        'url': icon['thumbnails'][0].get('url')
                    })
            #Save data in Project Modal
            attributes = {
                'color_palette': color_palette,
                'iconography': iconography,
                'brand_style': brand_style,
                'gradient_usage': gradient_usage,
                'imagery': imagery,
                'shadow_and_depth': shadow_and_depth,
                'line_thickness': line_thickness,
                'corner_rounding': corner_rounding,
            }
            project_data = {
                'attributes' : attributes,
                'f_icons': f_icons_list,
            }

            project_serializer_obj = ProjectSerializer(data=project_data)
            if project_serializer_obj.is_valid():
                project_serializer_obj.save()
                return Response(project_serializer_obj.data, status=status.HTTP_200_OK)
            return Response(custom_error_message(project_serializer_obj.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImageDownloadView(APIView):

    def get(self, request, *args, **kwargs):
        download_url = request.query_params.get('url')
        if not download_url:
            return Response({"error": "No download URL provided"}, status=status.HTTP_400_BAD_REQUEST)

        headers = {
            "Authorization": f"Bearer {settings.ICON_FINDER_KEY}"
        }
        response = requests.get(download_url, headers=headers)

        if response.status_code != 200:
            return Response({"error": "Failed to download image"}, status=response.status_code)

        image_content = response.content
        response = HttpResponse(
            image_content, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=image.png'
        return response


class DownloadFreePikView(APIView):

    def get(self, request, *args, **kwargs):
        icon_id = request.GET.get('id')
        if not icon_id:
            return Response({"error": "No icon ID provided"}, status=status.HTTP_400_BAD_REQUEST)

        url = f"https://api.freepik.com/v1/icons/{icon_id}/download"
        headers = {"x-freepik-api-key": "FPSX19dd1bf8e6534123a705ed38678cb8d1"}

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return Response({"error": "Failed to download icon"}, status=response.status_code)

        data = response.json()
        download_url = data["data"]["url"]

        # Download the actual image
        image_response = requests.get(download_url)
        if image_response.status_code != 200:
            return Response({"error": "Failed to download image from FreePik"}, status=image_response.status_code)

        image_content = image_response.content
        response = HttpResponse(
            image_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename={data["data"]["filename"]}.png'
        return response


class FigmaLinkProcessAPI(APIView):

    def post(self, request, *args, **kwargs):
        try:

            result = None
            feedback = None
            headers = {
                'X-Figma-Token': FIGMA_KEY
            }

            screen_link = request.data.get('screen_link')
            figma_link = request.data.get('figma_link')
            icon_color = request.data.get('icon_color', '')
            icon_style = request.data.get('icon_style', '')

            if not (screen_link or figma_link):
                return Response({"error": "No link provided"}, status=status.HTTP_400_BAD_REQUEST)
            if screen_link:
                pattern = r'/design/([^/]+)/.*\?node-id=([^&]+)'
                match = re.search(pattern, screen_link)
                if match:
                    FILE_KEY = match.group(1)
                    NODE_ID = match.group(2)

                FIGMA_API_URL = f'https://api.figma.com/v1/images/{FILE_KEY}?ids={NODE_ID}&format=png'

                response = requests.get(FIGMA_API_URL, headers=headers)
                if response.status_code == 200:
                    image_url = response.json()['images'][NODE_ID.replace('-', ':')]
                    image_response = requests.get(image_url)
                    if image_response.status_code == 200:
                        image_data = image_response.content
                        image_base64 = base64.b64encode(image_data).decode('utf-8')
                        result = process_image_data(image_base64)

            if figma_link:
                pattern = r'/design/([^/]+)/.*\?node-id=([^&]+)'
                match = re.search(pattern, figma_link)
                if match:
                    FILE_KEY = match.group(1)
                FIGMA_API_URL = f'https://api.figma.com/v1/files/{FILE_KEY}'
                response = requests.get(FIGMA_API_URL, headers=headers)
                if response.status_code == 200:
                    feedback = response.json()
                    data = {
                        'figma_url': FIGMA_API_URL,
                        'figma_response': feedback
                    }
                    return Response(data=data, status=status.HTTP_200_OK)

            color_palette = result.get("color_palette", "")
            iconography = result.get("iconography", "")
            brand_style = result.get("brand_style", "")
            gradient_usage = result.get("gradient_usage", "")
            imagery = result.get("imagery", "")
            shadow_and_depth = result.get("shadow_and_depth", "")
            line_thickness = result.get("line_thickness", "")
            corner_rounding = result.get("corner_rounding", "")

            f_query = f"{icon_color} {icon_style} {color_palette} {iconography} {brand_style} {gradient_usage} {imagery} {shadow_and_depth} {line_thickness} {corner_rounding}"

            # Freepik API request
            f_url = "https://api.freepik.com/v1/icons"
            querystring = {"term": f_query, "thumbnail_size": "24", "per_page": "10",
                           "page": "1", }
            f_headers = {
                "x-freepik-api-key": "FPSX19dd1bf8e6534123a705ed38678cb8d1"}

            f_response = requests.get(f_url, headers=f_headers, params=querystring)
            f_json_data = f_response.json()

            # Extract Freepik icon data
            f_icons_list = []
            for icon in f_json_data.get('data', []):
                if icon.get('thumbnails'):
                    f_icons_list.append({
                        'id': icon.get('id'),
                        'url': icon['thumbnails'][0].get('url')
                    })

            #Save data in Project Modal
            attributes = {
                'color_palette': color_palette,
                'iconography': iconography,
                'brand_style': brand_style,
                'gradient_usage': gradient_usage,
                'imagery': imagery,
                'shadow_and_depth': shadow_and_depth,
                'line_thickness': line_thickness,
                'corner_rounding': corner_rounding,
            }
            project_data = {
                'attributes' : attributes,
                'f_icons': f_icons_list,
                'screen_link': image_url,
            }

            project_serializer_obj = ProjectSerializer(data=project_data)
            if project_serializer_obj.is_valid():
                project_serializer_obj.save()

            return Response(project_serializer_obj.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Internal Server Error"}, status=status.HTTP_400_BAD_REQUEST)

class GetProjectListApi(APIView):
    def get(self, request, *args, **kwargs):
        project_list = Project.objects.all().order_by('-created_at')
        serializer = ProjectListSerializer(project_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetProjectIconListApi(APIView):
    def post(self, request, *args, **kwargs):
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({"error": "Project ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            project_list = Project.objects.get(id=project_id)
            serializer = ProjectIconListSerializer(project_list)
            return Response(serializer.data["f_icons"], status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({"error": "Project does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
