import base64
import io

from langchain_openai import ChatOpenAI
import zipfile
from io import BytesIO

from rest_framework.permissions import IsAuthenticated

from app.utils import process_image_data, is_image_url, custom_error_message, Color_Available_in_Filter, fetch_icons, format_value, \
    process_available_color_for_filter
from app.serializers import ProjectSerializer, ProjectListSerializer, ProjectIconListSerializer, ProjectHistorySerializer, IconSerializer
import re
import requests
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from app.models import Project
from auth_app.token_auth import CustomTokenAuthentication

OPENAI_API_KEY = settings.OPENAI_API_KEY
ICON_FINDER_KEY = settings.ICON_FINDER_KEY
FIGMA_KEY = settings.FIGMA_API_KEY
FREE_PIK_API_KEY = settings.FREE_PICK_API_KEY

fast_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt4o-mini", streaming=True)
import webcolors
from langchain.schema import HumanMessage

class ImageProcessView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            final_response_by_llm = None
            image_file = request.FILES.get('image')
            icon_color_hex, icon_color_name = request.data.get('icon_color'), None
            icon_style = request.data.get('icon_style')
            color_filter, style_filter = False, True if icon_style else False
            if not image_file:
                return Response({"error": "No image file provided"}, status=status.HTTP_400_BAD_REQUEST)

            image_data = image_file.read()
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            result = process_image_data(image_base64)
            print("Result of process_image_data")
            print(result)
            color_palette = format_value(result.get("color_palette", ""))
            iconography = format_value(result.get("iconography", ""))
            brand_style = format_value(result.get("brand_style", ""))
            gradient_usage = format_value(result.get("gradient_usage", ""))
            imagery = format_value(result.get("imagery", ""))
            shadow_and_depth = format_value(result.get("shadow_and_depth", ""))
            line_thickness = format_value(result.get("line_thickness", ""))
            corner_rounding = format_value(result.get("corner_rounding", ""))
            description = format_value(result.get("description", ""))

            #Extract Color from Hex Code
            if icon_color_hex:
                try:
                    color_name = webcolors.hex_to_name(icon_color_hex)
                    print("color_name")
                    print(color_name)
                    color_filter, icon_color_name = process_available_color_for_filter(color_name)
                except ValueError:
                    color_filter = False
            else:
                final_response_by_llm = process_available_color_for_filter(color_palette)
                if final_response_by_llm[0]:
                    color_filter, icon_color_name = final_response_by_llm
                else:
                    color_filter, icon_color_name = Color_Available_in_Filter(final_response_by_llm[1])


            #fetch Icons from free pik Api
            f_icons_list, result, error = fetch_icons(color_filter, style_filter, color_palette,
                                iconography, brand_style, gradient_usage, imagery,
                                shadow_and_depth, line_thickness, corner_rounding, description,
                                icon_color_name, icon_style)
            if error:
                    return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            # Generate keywords using the fast LLM with streaming enabled
            keywords = []
            try:
                # Initialize the fast LLM model
                fast_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4", streaming=True)
                
                # Create a prompt for generating keywords based on the image description
                prompt = HumanMessage(content=(
                    f"Generate keywords based on these image characteristics: {description}. "
                    f"Consider color palette: {color_palette}, style: {brand_style}, iconography: {iconography}, "
                    f"gradient usage: {gradient_usage}, imagery style: {imagery}."
                    f"Note: Only provide keywords, do not provide any other information."
                ))
                
                # Request keywords and handle the response stream
                response_stream = fast_llm.stream([prompt])
                for message in response_stream:
                    # Extract keywords from the message
                    keywords.extend(message.content.split(", "))
                
            except Exception as e:
                print("Error with ChatGPT API:", str(e))
                
            combined_response = ''.join(keywords)
            keywords = [keyword.strip().title() for keyword in combined_response.split(',') if keyword.strip()]
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
                'query_by_llm': result,
                'keywords': keywords
            }
            project_data = {
                'attributes' : attributes,
                'f_icons': f_icons_list,
                'keywords': keywords
            }

            project_serializer_obj = ProjectSerializer(data=project_data)
            if project_serializer_obj.is_valid():
                # print(project_serializer_obj)
                instance = project_serializer_obj.save()
                instance.user = request.user
                instance.save()
                return Response(project_serializer_obj.data, status=status.HTTP_200_OK)
            return Response(custom_error_message(project_serializer_obj.errors), status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(str(e))
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ImageDownloadView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

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
        response['Content-Disposition'] = 'attachment; filename=image.svg'
        return response


class DownloadFreePikView(APIView):
    authentication_classes = [CustomTokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        page_size = request.GET.get('page_size', '5')
        page = request.GET.get('page', '1')
        history_id = request.GET.get('history_id')
        if not page_size or not page or not history_id:
            return Response({"error": "No page size or page number provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            history_obj = Project.history.get(pk=history_id)
            serializer = ProjectHistorySerializer(history_obj)
            f_icons = serializer.data["f_icons"]
            page = int(page) if page else 1
            page_size = int(page_size) if page_size else 10

            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            icons_list = f_icons[start_index:end_index]

        except Project.history.model.DoesNotExist:
            return Response({"error": "History does not exist"}, status=status.HTTP_400_BAD_REQUEST)



        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w') as zf:
            for icon in icons_list:
                icon_id = icon["id"]
                icon_url = icon["url"]
                try:
                    # Download the actual image
                    image_response = requests.get(icon_url, timeout=10)
                    if image_response.status_code != 200:
                        continue  # Skip this icon if download fails

                    # Write the image to the zip file
                    zf.writestr(f"{icon_id}.png", image_response.content)

                except requests.exceptions.RequestException as e:
                    # Log the error and continue
                    print(f"Error while downloading icon {icon_id}: {str(e)}")
                    continue

        # Finalize the zip buffer
        zip_buffer.seek(0)

        # Return the zip file as an HTTP response
        response = HttpResponse(zip_buffer, content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=icons.zip'
        return response


class DownloadIconsZip(APIView):
    def post(self, request, *args, **kwargs):
        # Deserialize the input list of icons
        serializer = IconSerializer(data=request.data.get('icons', []), many=True)  # We expect 'icons' as key in the payload
        if not serializer.is_valid():
            return Response({"error": "Invalid data", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare an in-memory ZIP file
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for icon in serializer.validated_data:
                icon_id = icon['id']
                icon_url = icon['url']

                # Download the image
                try:
                    response = requests.get(icon_url)
                    response.raise_for_status()  # Raise an error for bad responses

                    # Get image content and write it to the ZIP file
                    image_content = response.content
                    zip_file.writestr(f"{icon_id}.png", image_content)
                except requests.RequestException as e:
                    return Response({"error": f"Failed to download {icon_url}: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Make sure we seek to the beginning of the buffer
        zip_buffer.seek(0)

        # Return the ZIP file as a response
        response = HttpResponse(zip_buffer.read(), content_type='application/zip')
        response['Content-Disposition'] = 'attachment; filename=icons.zip'
        return response

class FigmaLinkProcessAPI(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:

            result = None
            feedback = None
            headers = {
                'X-Figma-Token': FIGMA_KEY
            }

            screen_link = request.data.get('screen_link')
            figma_link = request.data.get('figma_link')
            icon_color_hex, icon_color_name = request.data.get('icon_color'), None
            icon_style = request.data.get('icon_style')
            color_filter, style_filter = False, True if icon_style else False

            if not (screen_link or figma_link):
                return Response({"error": "No link provided"}, status=status.HTTP_400_BAD_REQUEST)
            if screen_link:
                pattern = r'/design/([^/]+)/.*\?node-id=([^&]+)'
                match = re.search(pattern, screen_link)
                if match:
                    FILE_KEY = match.group(1)
                    NODE_ID = match.group(2)
                else:
                    return Response({"error": "Please Provide Valid Link"}, status=status.HTTP_400_BAD_REQUEST)

                FIGMA_API_URL = f'https://api.figma.com/v1/images/{FILE_KEY}?ids={NODE_ID}&format=png'

                response = requests.get(FIGMA_API_URL, headers=headers)
                if response.status_code == 404:
                    return Response({"error": "Figma Link Must be Public"}, status=status.HTTP_400_BAD_REQUEST)
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

            color_palette = format_value(result.get("color_palette", ""))
            iconography = format_value(result.get("iconography", ""))
            brand_style = format_value(result.get("brand_style", ""))
            gradient_usage = format_value(result.get("gradient_usage", ""))
            imagery = format_value(result.get("imagery", ""))
            shadow_and_depth = format_value(result.get("shadow_and_depth", ""))
            line_thickness = format_value(result.get("line_thickness", ""))
            corner_rounding = format_value(result.get("corner_rounding", ""))

            # Extract Color from Hex Code
            if icon_color_hex:
                try:
                    color_name = webcolors.hex_to_name(icon_color_hex)
                    print(color_name)
                    color_filter, icon_color_name = Color_Available_in_Filter(color_name)
                except ValueError:
                    color_filter = False

            f_icons_list, result, error = fetch_icons(color_filter, style_filter, color_palette,
                                       iconography, brand_style, gradient_usage, imagery,
                                       shadow_and_depth, line_thickness, corner_rounding,
                                       icon_color_name, icon_style)
            if error:
                    return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

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
                'query_by_llm': result
            }
            project_data = {
                'attributes' : attributes,
                'f_icons': f_icons_list,
                'screen_link': image_url,
            }

            project_serializer_obj = ProjectSerializer(data=project_data)
            if project_serializer_obj.is_valid():
                instance = project_serializer_obj.save()
                instance.user = request.user
                instance.save()
            return Response(project_serializer_obj.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))
            return Response({"error": "Internal Server Error"}, status=status.HTTP_400_BAD_REQUEST)

class ImageLinkProcessAPI(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            result = None
            feedback = None
            image_url = request.data.get('screen_link')
            icon_color_hex, icon_color_name = request.data.get('icon_color'), None
            icon_style = request.data.get('icon_style')
            color_filter, style_filter = False, True if icon_style else False

            if not image_url:
                return Response({"error": "No image URL provided"}, status=status.HTTP_400_BAD_REQUEST)

            # Check if the URL is an image
            if not self.is_image_url(image_url):
                return Response({"error": "The URL does not point to a valid image."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the image data
            response = requests.get(image_url)
            if response.status_code != 200:
                return Response({"error": "Failed to retrieve the image from the URL."}, status=status.HTTP_400_BAD_REQUEST)

            # Convert image to base64
            image_data = response.content
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            result = process_image_data(image_base64)

            # Process and save attributes
            color_palette = format_value(result.get("color_palette", ""))
            iconography = format_value(result.get("iconography", ""))
            brand_style = format_value(result.get("brand_style", ""))
            gradient_usage = format_value(result.get("gradient_usage", ""))
            imagery = format_value(result.get("imagery", ""))
            shadow_and_depth = format_value(result.get("shadow_and_depth", ""))
            line_thickness = format_value(result.get("line_thickness", ""))
            corner_rounding = format_value(result.get("corner_rounding", ""))
            description = format_value(result.get("description", ""))

            # Extract color from hex code if provided
            if icon_color_hex:
                try:
                    color_name = webcolors.hex_to_name(icon_color_hex)
                    color_filter, icon_color_name = Color_Available_in_Filter(color_name)
                except ValueError:
                    color_filter = False

            # Fetch icons with specified filters
            f_icons_list, result, error = fetch_icons(
                color_filter, style_filter, color_palette, iconography,
                brand_style, gradient_usage, imagery, shadow_and_depth,
                line_thickness, corner_rounding, icon_color_name, icon_style
            )
            if error:
                return Response({"error": error}, status=status.HTTP_400_BAD_REQUEST)

            # Generate keywords using the fast LLM with streaming enabled
            keywords = []
            try:
                # Initialize the fast LLM model
                fast_llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4", streaming=True)
                
                # Create a prompt for generating keywords based on the image description
                prompt = HumanMessage(content=( 
                    f"Generate keywords based on these image characteristics: {description}. "
                    f"Consider color palette: {color_palette}, style: {brand_style}, iconography: {iconography}, "
                    f"gradient usage: {gradient_usage}, imagery style: {imagery}."
                ))
                
                # Request keywords and handle the response stream
                response_stream = fast_llm.stream([prompt])
                for message in response_stream:
                    # Extract keywords from the message
                    keywords.extend(message.content.split("\n"))
                    
            except Exception as e:
                print("Error with ChatGPT API:", str(e))
                
            # Clean up the response and convert it into a list of valid keywords
            keywords = [keyword.strip().title() for keyword in keywords if keyword.strip() and not keyword.strip().isdigit()]

            # Optional: remove duplicates
            keywords = list(set(keywords))
            # Prepare data to save in the Project model
            attributes = {
                'color_palette': color_palette,
                'iconography': iconography,
                'brand_style': brand_style,
                'gradient_usage': gradient_usage,
                'imagery': imagery,
                'shadow_and_depth': shadow_and_depth,
                'line_thickness': line_thickness,
                'corner_rounding': corner_rounding,
                'query_by_llm': result,
                'keywords': keywords
                
            }
            project_data = {
                'attributes': attributes,
                'f_icons': f_icons_list,
                'image_url': image_url,
            }

            # Serialize and save project data
            project_serializer_obj = ProjectSerializer(data=project_data)
            if project_serializer_obj.is_valid():
                instance = project_serializer_obj.save()
                instance.user = request.user
                instance.save()
            return Response(project_serializer_obj.data, status=status.HTTP_200_OK)
        except Exception as e:
            print(str(e))
            return Response({"error": "Internal Server Error"}, status=status.HTTP_400_BAD_REQUEST)
    def is_image_url(self, url: str) -> bool:
        try:
            # Send a HEAD request to the URL to fetch only the headers
            response = requests.head(url, allow_redirects=True)
            
            # Get the Content-Type header to check if it contains 'image'
            content_type = response.headers.get('Content-Type', '')
            return 'image' in content_type
        except requests.RequestException:
            return False

class SimilarIconSearchAPI(APIView):
    authentication_classes = [CustomTokenAuthentication]
    # permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            # Get the icon_id from the request data
            icon_id = request.data.get("icon_id")
            if not icon_id:
                return Response({"error": "Icon ID is required."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch the icon details using the icon_id
            icon_details = self.get_icon_details(icon_id)
            if not icon_details:
                return Response({"error": "Icon not found."}, status=status.HTTP_404_NOT_FOUND)

            # Get related icons from the response
            related_icons = icon_details.get("data", {}).get("related", {}).get("style", [])
            if not related_icons:
                return Response({"error": "No related icons found."}, status=status.HTTP_404_NOT_FOUND)

            similar_icons = [
                {
                    "icon_id": icon_id,
                    "similar_icon_id": icon["id"],
                    "similar_icon_family_id": icon["family"]["id"],
                    "url": icon.get("thumbnails", [{}])[0].get("url", "")  # The first thumbnail URL is selected
                }
                for icon in related_icons
            ]

            return Response({"similar_icons": similar_icons}, status=status.HTTP_200_OK)

        except Exception as e:
            print(str(e))
            return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_icon_details(self, icon_id):
        try:
            headers = {"x-freepik-api-key": f"{FREE_PIK_API_KEY}"}
            response = requests.get(
                f"https://api.freepik.com/v1/icons/{icon_id}", headers=headers
            )
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except requests.RequestException as e:
            print("Error fetching icon details:", e)
            return None


# class SimilarIconSearchAPI(APIView):
#     authentication_classes = [CustomTokenAuthentication]
#     # permission_classes = [IsAuthenticated]

#     def post(self, request, *args, **kwargs):
#         try:
#             # Get the icon_id from the request data
#             icon_id = request.data.get('icon_id')
#             if not icon_id:
#                 return Response({"error": "Icon ID is required."}, status=status.HTTP_400_BAD_REQUEST)

#             # Fetch the icon details using the icon_id (You would use Freepik's API here to fetch icon details)
#             icon_details = self.get_icon_details(icon_id)
#             if not icon_details:
#                 return Response({"error": "Icon not found."}, status=status.HTTP_404_NOT_FOUND)

#             # Get the family ID of the icon
#             family_id = icon_details['data']['family']['id']
            
#             if family_id:
#                 print(f"Family ID: {family_id}")
#             if not family_id:
#                 return Response({"error": "Icon family ID is missing."}, status=status.HTTP_400_BAD_REQUEST)

#             # Fetch similar icons by family ID
#             similar_icons = self.get_similar_icons_by_family(family_id)
#             if not similar_icons:
#                 return Response({"error": "No similar icons found."}, status=status.HTTP_404_NOT_FOUND)

#             # Prepare the response data (e.g., return the similar icons)
#             return Response({"similar_icons": similar_icons}, status=status.HTTP_200_OK)
        
#         except Exception as e:
#             print(str(e))
#             return Response({"error": "Internal Server Error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

#     def get_icon_details(self, icon_id):
#         try:
#             headers = {"x-freepik-api-key": f'{FREE_PIK_API_KEY}'}
#             response = requests.get(f'https://api.freepik.com/v1/icons/{icon_id}', headers=headers)
#             if response.status_code == 200:
#                 return response.json()
#             else:
#                 return None
#         except requests.RequestException as e:
#             print("Error fetching icon details:", e)
#             return None

#     def get_similar_icons_by_family(self, family_id):
#         # Ensure the API key is passed in securely (assuming it's set as an environment variable)
#         try:
#             headers = {"x-freepik-api-key": f'{FREE_PIK_API_KEY}'}
#             querystring = {"family-id": family_id, "per_page":"100"}
            
#             # Make the GET request to Freepik API
#             response = requests.get(f'https://api.freepik.com/v1/icons', headers=headers, params=querystring)
            
#             # Check if the response status code is 200 (successful)
#             if response.status_code == 200:
#                 # Try to extract the icons from the response JSON
                
#                 response_data = response.json()
#                 if 'data' in response_data:
#                     icons = []
#                     for item in response_data['data']:
#                         for thumbnail in item['thumbnails']:
#                             icons.append({
#                                 'id': item['id'],
#                                 'url': thumbnail['url']
#                             })
#                     return icons
#                 else:
#                     print(f"Error: 'icons' key not found in response data.")
#                     return None
#             else:
#                 print(f"Error: Received status code {response.status_code} - {response.text}")
#                 return None

#         except requests.RequestException as e:
#             # Handle any exceptions that may arise during the API call
#             print("Error fetching similar icons:", e)
#             return None



class GetProjectListApi(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        project_list = Project.objects.filter(user=request.user).all().order_by('-created_at')
        serializer = ProjectListSerializer(project_list, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class GetProjectIconListApi(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            project_id = request.data.get('project_id')
            page = request.data.get('page')
            page_size = request.data.get('page_size')

            if not project_id:
                return Response({"error": "Project ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            try:
                project_list = Project.objects.get(id=project_id, user=request.user)
            except Project.DoesNotExist:
                return Response({"error": "Project does not exist"}, status=status.HTTP_400_BAD_REQUEST)

            serializer = ProjectIconListSerializer(project_list)

            f_icons = serializer.data["f_icons"]
            page = int(page) if page else 1
            page_size = int(page_size) if page_size else 10

            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_f_icons = f_icons[start_index:end_index]

            response_data = {
                "count": len(f_icons),
                "results": paginated_f_icons
            }

            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangeProjectName(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({"error": "Please Provide Project Id"}, status.HTTP_400_BAD_REQUEST)
            project_obj = Project.objects.get(id=project_id, user=request.user)
            project_new_name = request.data.get('new_name', project_obj.name)
            project_obj.name = project_new_name
            project_obj.save()
            return Response({"data": "Project Renamed Successfully"}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({"error": "Project does not exist"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class GetProjectHistoryListApi(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            project_id = request.data.get('project_id')
            if not project_id:
                return Response({"error": "Please Provide Project Id"}, status.HTTP_400_BAD_REQUEST)
            project_obj = Project.objects.get(pk=project_id, user=request.user)
        except Project.DoesNotExist:
            return Response({"detail": "Project Does Not Exist"}, status=status.HTTP_404_NOT_FOUND)

        history = project_obj.history.all()
        serializer = ProjectHistorySerializer(history, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetHistoryByHistoryIdApi(APIView):
    authentication_classes = [CustomTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        history_id = request.data.get('history_id')
        page = request.data.get('page')
        page_size = request.data.get('page_size')
        if not history_id:
            return Response({"error": "History ID is required"}, status.HTTP_400_BAD_REQUEST)
        try:
            history_obj = Project.history.get(pk=history_id)
            serializer = ProjectHistorySerializer(history_obj)
            f_icons = serializer.data["f_icons"]
            page = int(page) if page else 1
            page_size = int(page_size) if page_size else 10

            start_index = (page - 1) * page_size
            end_index = start_index + page_size
            paginated_f_icons = f_icons[start_index:end_index]

            response_data = {
                "count": len(f_icons),
                "results": paginated_f_icons
            }
            return Response(response_data, status=status.HTTP_200_OK)
        except Project.history.model.DoesNotExist:
            return Response([], status=status.HTTP_200_OK)





