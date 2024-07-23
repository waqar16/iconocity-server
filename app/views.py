import base64
import requests
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.conf import settings
from langchain_openai import ChatOpenAI
from app.utils import process_image_data
import re
import requests
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

OPENAI_API_KEY = settings.OPENAI_API_KEY
ICON_FINDER_KEY = settings.ICON_FINDER_KEY
FIGMA_KEY = settings.FIGMA_API_KEY
fast_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", streaming=True)


class ImageProcessView(APIView):

    def post(self, request, *args, **kwargs):
        image_file = request.FILES.get('image')
        if not image_file:
            return Response({"error": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)

        image_data = image_file.read()
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        result = process_image_data(image_base64)

        style = result.get("style", "")
        category = result.get("category", "")
        context = result.get("context", "")
        content_specifics = result.get("content_specifics", "")
        technical_aspects = result.get("technical_aspects", "")

        f_query = f"{style} {category} {context} {content_specifics} {technical_aspects}"
        query = f"{style}"

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

        response_data = {
            'attributes': {
                'style': style,
                'category': category,
                'context': context,
                'content_specifics': content_specifics,
                'technical_aspects': technical_aspects
            },
            'icons': icon_data_list,
            'f_icons': f_icons_list
        }

        return Response(response_data, status=status.HTTP_200_OK)


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
        result = None
        feedback = None
        headers = {
            'X-Figma-Token': FIGMA_KEY
        }

        screen_link = request.data.get('screen_link')
        figma_link = request.data.get('figma_link')
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

        style = result.get("style", "")
        category = result.get("category", "")
        context = result.get("context", "")
        content_specifics = result.get("content_specifics", "")
        technical_aspects = result.get("technical_aspects", "")

        f_query = f"{style} {category} {context} {content_specifics} {technical_aspects}"

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

        response_data = {
            'attributes': {
                'style': style,
                'category': category,
                'context': context,
                'content_specifics': content_specifics,
                'technical_aspects': technical_aspects
            },
            'f_icons': f_icons_list,
            'screen_link': image_url,
            'figma_link': feedback,
        }

        return Response(response_data, status=status.HTTP_200_OK)
