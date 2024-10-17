from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from app.models import Project
from app.serializers import ProjectIconAttributesSerializer
from auth_app.token_auth import CustomTokenAuthentication
from query.utils import ChangeIconQueryBot
from app.utils import fetch_icons


class UpdateIconAttributesByQuery(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_id = request.data['project_id']
        query = request.data['query']
        language = 'English'
        if not project_id:
            return Response({'error': 'Please Provide Project Id'}, status=400)


        try:
            project_instance = Project.objects.get(id=project_id, user=request.user)
            serializer = ProjectIconAttributesSerializer(project_instance)
            project_attributes = serializer.data["attributes"]
            print("before attributes-->", project_attributes)
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

            f_icons_list, result = fetch_icons(False, False, attributes["color_palette"],
                                       attributes["iconography"], attributes["brand_style"] , attributes["gradient_usage"],
                                       attributes["imagery"], attributes["shadow_and_depth"], attributes["line_thickness"], attributes["corner_rounding"])

            project_instance.f_icons = f_icons_list
            project_instance.attributes = attributes
            project_instance.save_with_historical_record()

            return Response(response.response, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': "Project Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)