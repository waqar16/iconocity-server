from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from app.models import Project
from app.serializers import ProjectIconAttributesSerializer, ProjectSerializer, ProjectWithHistorySerializer
from query.utils import ChangeIconQueryBot
from app.utils import custom_error_message
# Create your views here.

class UpdateIconAttribuesByQuery(APIView):
    def post(self, request):
        project_id = request.data['project_id']
        query = request.data['query']
        language = 'English'
        if not project_id:
            return Response({'error': 'Please Provide Project Id'}, status=400)


        try:
            project_instance = Project.objects.get(id=project_id)
            serializer = ProjectIconAttributesSerializer(project_instance)
            project_attributes = serializer.data["attributes"]
            print("before attribues-->", project_attributes)
            response = ChangeIconQueryBot(query, project_attributes, language)
            print(response)
            attributes = {
                'color_palette': response.color_palette if response.color_palette else project_attributes["color_palette"],
                'iconography': response.iconography if response.iconography else project_attributes["iconography"],
                'brand_style': response.brand_style if response.brand_style else project_attributes["brand_style"],
                'gradient_usage': response.gradient_usage if response.gradient_usage else project_attributes["gradient_usage"],
                'imagery': response.imagery if response.imagery else project_attributes["imagery"],
                'shadow_and_depth': response.shadow_and_depth if response.shadow_and_depth else project_attributes["shadow_and_depth"],
                'line_thickness': response.line_thickness if response.line_thickness else project_attributes["line_thickness"],
                'corner_rounding': response.corner_rounding if response.corner_rounding else project_attributes["corner_rounding"],
            }
            f_query = " ".join(attributes.values())
            print(f_query)
            querystring = {"term": f_query, "thumbnail_size": "256", "per_page": "10",
                               "page": "1", }

            # Freepik API request
            f_url = "https://api.freepik.com/v1/icons"
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
                    if len(f_icons_list) >= 150:
                        break

            project_data = {
                'attributes': attributes,
                'f_icons': f_icons_list,
            }

            project_serializer_obj = ProjectWithHistorySerializer(project_instance, data=project_data, partial=True)
            if project_serializer_obj.is_valid():
                project_serializer_obj.save()
                return Response(response.response, status=status.HTTP_200_OK)
            return Response(custom_error_message(project_serializer_obj.errors), status=status.HTTP_400_BAD_REQUEST)
        except Project.DoesNotExist:
            return Response({'error': "Project Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)