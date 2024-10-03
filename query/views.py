from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from app.models import Project
from app.serializers import ProjectIconAttributesSerializer, ProjectSerializer, ProjectWithHistorySerializer, \
    ProjectUpdateSerializer
from query.utils import ChangeIconQueryBot
from app.utils import custom_error_message, fetch_icons
from rest_framework.viewsets import ModelViewSet
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
            if not response.isRelated:
                return Response(response.response, status=status.HTTP_200_OK)
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
            print("after update->", attributes)

            f_icons_list = fetch_icons(False, False, attributes["color_palette"],
                                       attributes["iconography"], attributes["brand_style"] , attributes["gradient_usage"],
                                       attributes["imagery"], attributes["shadow_and_depth"], attributes["line_thickness"], attributes["corner_rounding"])

            project_data = {
                'attributes': attributes,
                'f_icons': f_icons_list,
            }
            project_instance.f_icons = f_icons_list
            project_instance.attributes = attributes
            project_instance.save_with_historical_record()

            # # project_serializer_obj = ProjectUpdateSerializer(project_instance, data=project_data, partial=True)
            # # if project_serializer_obj.is_valid(raise_exception=True):
            # #     project_serializer_obj.save()
            #     print("saved", project_serializer_obj.data["attributes"])
            return Response(response.response, status=status.HTTP_200_OK)
            # return Response(custom_error_message(project_serializer_obj.errors), status=status.HTTP_400_BAD_REQUEST)
        except Project.DoesNotExist:
            return Response({'error': "Project Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)