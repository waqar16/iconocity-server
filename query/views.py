from http.client import responses

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from app.models import Project
from app.serializers import ProjectIconAttributesSerializer, ProjectSerializer
from auth_app.token_auth import CustomTokenAuthentication
from query.utils import GeneralQueryAnswer, IdentifyQuery, changeIconColorAndShapeQueryBot
from app.utils import fetch_icons, format_value


class UpdateIconAttributesByQuery(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        attributes = {}
        isRelatedColor, isRelatedShape = False, False
        general_response = None
        project_id = request.data.get('project_id')
        query = request.data.get('query')
        
        if not query:
            return Response({'error': 'Please Provide Query'}, status=400)
        if not project_id:
            return Response({'error': 'Please Provide Project Id'}, status=400)


        try:
            icon_style = None
            icon_color_name = None
            # project_instance = Project.objects.last()
            project_instance = Project.objects.get(id=project_id, user=request.user)

            if not project_instance:
                return Response({'error': 'Project Does Not Exist'}, status=400)
            serializer = ProjectIconAttributesSerializer(project_instance)
            # print("serializer data:", serializer.data)
            project_attributes = serializer.data["attributes"]
            print("before attributes-->", project_attributes)
            print("before f_icons-->", project_instance.f_icons[0])
            response = IdentifyQuery(query)
            
            print("response-->", response)

            # Check if the response path is valid and has the necessary data
            if not response or not response.path:
                return Response({'error': 'Invalid query response, path is missing'}, status=400)

            # Process the response based on the path
            if response.path == 'general':
                actual_response = GeneralQueryAnswer(query, project_attributes)
                if not actual_response:
                    return Response({'error': 'General query processing failed'}, status=400)
                print(f"Actual response from LLM: {actual_response}")
                general_response = actual_response.general_response
                attributes['color_palette'] = format_value(actual_response.color_palette)
                attributes['iconography'] = format_value(actual_response.iconography)
                attributes['brand_style'] = format_value(actual_response.brand_style)
                attributes['gradient_usage'] = format_value(actual_response.gradient_usage)
                attributes['imagery'] = format_value(actual_response.imagery)
                attributes['shadow_and_depth'] = format_value(actual_response.shadow_and_depth)
                attributes['line_thickness'] = format_value(actual_response.line_thickness)
                attributes['corner_rounding'] = format_value(actual_response.corner_rounding)
            else:
                attributes = project_attributes

            if response.path == 'color':
                isRelatedColor = True
                actual_response = changeIconColorAndShapeQueryBot(query)
                icon_color_name = actual_response.color if actual_response.color else None
                general_response = actual_response.general_response
                icon_style = None                

            if response.path == 'shape':
                isRelatedShape = True
                actual_response = changeIconColorAndShapeQueryBot(query)
                icon_style = actual_response.shape if actual_response.shape else None
                general_response = actual_response.general_response
                icon_color_name = None
            
            print("after attributes-->", attributes)

            f_icons_list, result, error = fetch_icons(
                isRelatedColor, isRelatedShape, attributes["color_palette"],
                attributes["iconography"], attributes["brand_style"] , attributes["gradient_usage"],
                attributes["imagery"], attributes["shadow_and_depth"], attributes["line_thickness"],
                attributes["corner_rounding"], icon_color_name, icon_style
            )
            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the 'attributes' has meaningful data (non-empty values)
            if any(value != "" for value in attributes.values()):
                project_instance.attributes = attributes

            if f_icons_list:
                print("f_icons_list_old-->", project_instance.f_icons[0])
                project_instance.f_icons = f_icons_list
                print("f_icons_list_new-->", f_icons_list[0])

            # Save the project instance and record changes in history
            project_instance.save_with_historical_record()
            project_instance.refresh_from_db()
            project_instance.skip_history_when_saving = True
                

            response_serializers = ProjectIconAttributesSerializer(project_instance)
            data = response_serializers.data
            data['query_response'] = general_response
            data['query_string'] = result
            return Response(data=data, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'error': "Project Does Not Exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)