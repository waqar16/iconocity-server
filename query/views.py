from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from app.models import Project
from app.serializers import ProjectIconAttributesSerializer, ProjectSerializer
from auth_app.token_auth import CustomTokenAuthentication
from query.utils import ChangeIconQueryBot, changeIconColorAndShapeQueryBot
from app.utils import fetch_icons, format_value


class UpdateIconAttributesByQuery(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        project_id = request.data['project_id']
        query = request.data['query']
        if not project_id:
            return Response({'error': 'Please Provide Project Id'}, status=400)


        try:
            icon_style = None
            icon_color_name = None
            project_instance = Project.objects.last()
            # project_instance = Project.objects.get(id=project_id, user=request.user)
            serializer = ProjectIconAttributesSerializer(project_instance)
            project_attributes = serializer.data["attributes"]
            print("before attributes-->", project_attributes)
            response = changeIconColorAndShapeQueryBot(query)

            if not response.isRelatedColor and not response.isRelatedShape:
                data = {
                    'query_response': response.general_response
                }
                return Response(data=data, status=status.HTTP_200_OK)

            attributes = {
                'color_palette': project_attributes["color_palette"],
                'iconography': project_attributes["iconography"],
                'brand_style': project_attributes["brand_style"],
                'gradient_usage': project_attributes["gradient_usage"],
                'imagery': project_attributes["imagery"],
                'shadow_and_depth': project_attributes["shadow_and_depth"],
                'line_thickness': project_attributes["line_thickness"],
                'corner_rounding': project_attributes["corner_rounding"],
            }

            if response.isRelatedColor:
                icon_color_name = response.color
            else:
                icon_color_name = response.color if response.color else project_attributes["color_palette"]

            if response.isRelatedShape:
                icon_style = response.shape

            f_icons_list, result, error = fetch_icons(response.isRelatedColor, response.isRelatedShape, attributes["color_palette"],
                                       attributes["iconography"], attributes["brand_style"] , attributes["gradient_usage"],
                                       attributes["imagery"], attributes["shadow_and_depth"], attributes["line_thickness"],
                                               attributes["corner_rounding"], icon_color_name, icon_style)
            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            if f_icons_list:
                project_instance.f_icons = f_icons_list
            if attributes:
                project_instance.attributes = attributes
            project_instance.save_with_historical_record()
            response_serializers = ProjectIconAttributesSerializer(project_instance)
            data = response_serializers.data
            data['query_response'] = response.general_response
            data['query_string'] = result
            return Response(data=data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': "Project Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)