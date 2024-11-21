from typing import Literal

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains import TransformChain
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from django.conf import settings
import requests
from difflib import get_close_matches
from pydantic import ValidationError

model = ChatOpenAI(temperature=0.5, model="gpt-4o-mini", max_tokens=1024)

class ImageInformation(BaseModel):
    color_palette: str = Field(description="The primary color palette from the picture")
    iconography: str = Field(description="The iconography of the picture")
    brand_style: str = Field(description="The band style of the picture")
    gradient_usage: str = Field(description="The gradient usage of the picture")
    imagery: str = Field(description="The imagery of the picture")
    shadow_and_depth: str = Field(description="The shadow and depth of the picture")
    line_thickness: str = Field(description="The line thickness of the picture")
    corner_rounding: str = Field(description="The corner rounding of the picture")
    description: str = Field(description="The description of the picture")

parser = JsonOutputParser(pydantic_object=ImageInformation)


def process_image_data(image_base64: str):
    vision_prompt = """Instruction:
    Analyze the design to extract specific visual attributes. 
    Review the design carefully and identify the following 
    attributes:
    
    1.Color Palette:
    • Identify the primary color used in the design.
    • Determine the accent color that complements the primary palette.
    • Note the background color.
    • Assess the contrast level (high contrast vs. low contrast).
    • Get Major color only, and it should be only one color name
    
    2. Iconography:
    • Check if the design includes any icons.
    • Identify the style of the icons (choose one: Flat, Outline, Filled).
    • Observe the relative size of the icons (choose one: Small, Medium, Large).
    • Describe the shape of the icons (choose one: Rounded, Square, Freeform).
        
    3.Brand Style:
    • Determine the overall style and tone of the design.
        Categorize it as one of the following:
        • Corporate: Formal, professional, typically used for business or financial services.
        • Casual: Friendly, relaxed, often seen in lifestyle or personal brand designs.
        • Modern: Minimalistic, clean, often characterized by simplicity and elegance.
        • Playful: Vibrant, fun, colorful, often used for children’s products or entertainment brands.
        If the design represents a specific industry (e.g., healthcare, technology, education), specify that \
        industry as the brand style** (e.g., "Healthcare," "Technology," "Education"). Identify the industry based \
        on any specific visual cues, symbols, or elements related to that field (e.g., stethoscopes for healthcare, \
        computers for technology).


    4. Imagery:
    • Note the style of imagery used (choose one: Illustrative, Photorealistic).
    • Identify the theme of the imagery (choose one: Nature, Technology, Abstract).
    
    5. Gradient Usage:
    • Detect the presence of gradients in the design.
    • If gradients are present, identify the direction (choose one: Linear, Radial) and the dominant gradient color stop.
    • If no gradients are present, label this as "None".
    
    6. Shadow and Depth:
    • Check for the use of shadows (choose one: Drop shadows, Inner shadows, None).
    • Determine the depth effect created by these shadows (choose one: Flat, Elevated).

    7. Line Thickness:
    • Assess the consistency of line weight throughout the design (choose one: Thick, Thin, Variable).

    8. Corner Rounding:
    •  Identify the degree of corner rounding in shapes (choose one: Sharp corners, Slightly rounded, Fully rounded).

    9. Description:
    •  Description should contain up to 10 nouns that best describe the content. Rank the nouns for description according to how well they describe the picture. Give description as single string with list of up to 10 nouns separated by comma, without numbering and new line.

    
    Output:
    • For each of the above attributes, populate the results as a single keyword representing the attribute detected. \
    Avoid using non-descriptive answers like "Yes" or "No"; instead, specify relevant details or use "None" where \
    applicable.
    Example Output:
        • Color Palette: Blue, Yellow, White, High Contrast
        • Iconography: Flat, Medium, Rounded
        • Brand Style: Corporate
        • Imagery: Illustrative, Technology
        • Gradient Usage: Linear, Blue-Yellow
        • Shadow and Depth: Drop shadows, Elevated
        • Line Thickness: Thin
        • Corner Rounding: Slightly rounded
        • Description: boxing, gloves, club, website, training, excellence, athletes, sport, youth, sessions"""

    # chain decorator to make it runnable
    @chain
    def image_model(inputs: dict):
        msg = model.invoke(
            [HumanMessage(
                content=[
                    {"type": "text", "text": inputs["prompt"]},
                    {"type": "text", "text": parser.get_format_instructions()},
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{inputs['image']}"}},
                ])]
        )
        print("Milos msg.content in utils.py")
        print(msg.content)
        return msg.content

    load_image_chain = TransformChain(
        input_variables=["image"],
        output_variables=["image"],
        transform=lambda x: {"image": image_base64}
    )

    vision_chain = load_image_chain | image_model | parser
    milos_chain = load_image_chain | image_model
    print("Milos load_image_chain in utils.py")
    print(milos_chain.invoke({'image': image_base64, 'prompt': vision_prompt}))
    return vision_chain.invoke({'image': image_base64, 'prompt': vision_prompt})



def is_image_url(self, url: str) -> bool:
    try:
        # Send a HEAD request to the URL to fetch only the headers
        response = requests.head(url, allow_redirects=True)
        
        # Get the Content-Type header to check if it contains 'image'
        content_type = response.headers.get('Content-Type', '')
        return 'image' in content_type
    except requests.RequestException:
        return False

def custom_error_message(errors):
    for key, value in errors.items():
        if isinstance(value, list):
            return {'error': value[0].replace('field', key + ' field')}
        elif isinstance(value, dict):
            return custom_error_message(value)
    return {'error': 'Unknown error'}


def Color_Available_in_Filter(color):
    Valid_Filter_list_FREEPIK = [
        'gradient',
        'solid-black',
        'multicolor',
        'blue',
        'azure',
        'black',
        'chartreuse',
        'cyan',
        'gray',
        'green',
        'orange',
        'red',
        'rose',
        'spring-green',
        'violet',
        'white',
        'yellow',
    ]
    if color in Valid_Filter_list_FREEPIK:
        return True, color
    return False, color
# def process_available_color_for_filter(color: str):
#     class ResponseStructure(BaseModel):
#         color: Literal[
        # 'gradient',
        # 'solid-black',
        # 'multicolor',
        # 'blue',
        # 'azure',
        # 'black',
        # 'chartreuse',
        # 'cyan',
        # 'gray',
        # 'green',
        # 'orange',
        # 'red',
        # 'rose',
        # 'spring-green',
        # 'violet',
        # 'white',
        # 'yellow',
#         ] = Field(description="Exact or closest color.")
#         is_available: bool = Field(default=False, description="True if color matches or has a close match.")

#     def find_most_similar_color(color_input: str) -> str:
#         allowed_colors = [
#             'blue', 'black', 'cyan', 'chartreuse', 'azure', 'gray', 
#             'green', 'orange', 'red', 'rose', 'spring-green', 'violet', 'white', 'yellow'
#         ]
        
#         color_input = color_input.lower()
#         matches = get_close_matches(color_input, allowed_colors, n=1, cutoff=0.5)
#         return matches[0] if matches else "gray"
    

#     # Preprocess the input color by finding the closest match
#     similar_color = find_most_similar_color(color)

#     template = """
#         You are an AI assistant tasked with identifying the exact or closest match from a list of colors Literal.

#         Instructions:
#           1. If the color provided matches exactly with one of the given colors Literal, return True and the color.
#           2. If the color does not match exactly but is close in name or shade to one of the colors Literal, return True and the closest matching color.
#           3. If no close match is found, return False and the original color given as input.
#     """

#     structured_llm = model.with_structured_output(ResponseStructure)
#     prompt = ChatPromptTemplate.from_messages([
#         ("system", template), 
#         MessagesPlaceholder("history", optional=True), 
#         ("human", "{question}")
#     ])
#     partial_prompt = prompt.partial(language='English', query=similar_color)
#     chain = partial_prompt | structured_llm

#     try:
#         response = chain.invoke({"question": similar_color})
#         return response.is_available, response.color
#     except ValidationError as e:
#         # Handle unexpected errors gracefully
#         return False, "gray"  # Default fallback to a valid color
    
   
   
   
   
    
    
# Defining the valid Freepik colors
freepik_colors = [
    'gradient', 'solid-black', 'multicolor', 'blue', 'azure', 'black', 'chartreuse',
    'cyan', 'gray', 'green', 'orange', 'red', 'rose', 'spring-green', 'violet', 'white', 'yellow'
]

# Helper function to find the closest match (basic implementation based on substring matching)
def get_closest_color(input_color: str) -> str:
    for color in freepik_colors:
        if input_color.lower() in color:
            return color
    return input_color  # Return the original input if no close match found

def process_available_color_for_filter(color: str):
    class ResponseStructure(BaseModel):
        color: Literal[
            'blue', 'black', 'cyan', 'chartreuse', 'azure', 'gray', 'green', 'orange', 'red', 'rose',
            'spring-green', 'violet', 'white', 'yellow', 'gradient', 'solid-black', 'multicolor'
        ] = Field(description="Find the exact or closest color from input query.")
        is_available: bool = Field(default=False, description="Indicates if color is available or matches the closest color.")

    template = """
        You are an AI assistant tasked with identifying the exact or closest match from a list of valid colors.

        Instructions:
          1. If the color provided matches exactly with one of the valid colors, return True and the color.
          2. If the color does not match exactly but is close in name or shade to one of the valid colors, return True and the closest match.
          3. If no close match is found, return False and the original input color.
    """

    # Enhanced matching logic
    closest_color = get_closest_color(color)
    is_available = closest_color in freepik_colors

    response = ResponseStructure(
        color=closest_color if is_available else color,
        is_available=is_available
    )
    return response.is_available, response.color






    
    
# def process_available_color_for_filter(color: str):
#     class ResponseStructure(BaseModel):
#         color: Literal['blue', 'black', 'cyan', 'chartreuse', 'azure', 'gray', 'green', 'orange', 'red', 'rose',
#                    'spring-green', 'violet', 'white', 'yellow'] = Field(
#             description="Find the exact color or closet color from input query."
#         )
#         is_available: bool = Field(default=False, description="if color is available or match the closets colors, return True otherwise False")

#     template = """
#         You are an AI assistant tasked with identifying the exact or closest match from a list of colors Literal.

#         Instructions:
#           1. If the color provided matches exactly with one of the given colors Literal, return True and the color.
#           2. If the color does not match exactly but is close in name or shade to one of the colors Literal, return True and the closest matching color.
#           3. If no close match is found, return False and the original color given as input.
#     """

#     structured_llm = model.with_structured_output(ResponseStructure)
#     prompt = ChatPromptTemplate.from_messages(
#         [
#             ("system", template),
#             MessagesPlaceholder("history", optional=True), ("human", "{question}")
#         ]
#     )

#     partial_prompt = prompt.partial(language='English', query=color)
#     chain = partial_prompt | structured_llm
#     response = chain.invoke({"question": color})
#     return response.is_available, response.color

def process_icons_query(inputs: str):

    prompt = """
    Create a brief query string incorporating the following given string. Consider the below examples output.
    
    Examples Output:
        1.  The design features a corporate technology theme with a dominant black color. It incorporates flat, modern
            icons and illustrative imagery of innovation, including a brain symbol. Linear gradients and drop shadows
            create an elevated, clean look, with thin lines and slightly rounded corners adding to the professional
            aesthetic.
            
        2. The design embraces a minimalist, nature-inspired theme with a dominant earthy green color palette. It uses
           hand-drawn, organic icons and photographic imagery of landscapes, trees, and sustainability. Soft shadows and
           subtle textures provide depth, while rounded edges and natural elements create a welcoming and eco-friendly
           aesthetic. The overall feel is calm and harmonious, aimed at conveying environmental awareness and simplicity.
           
        3. This design is driven by a futuristic, tech-heavy theme, featuring a vibrant neon blue and metallic silver
           color scheme. It incorporates 3D icons and dynamic, animated graphics such as data streams and digital grids.
           Bold typography, sharp geometric shapes, and high-contrast backgrounds give the design an energetic,
           cutting-edge look, evoking innovation and speed. The interface uses glass morphism effects with transparent
           layers and glowing edges to emphasize the modern, forward-thinking aesthetic.
           
    Here is the:\n\n {context}\n\n
    """

    model = ChatOpenAI(temperature=0.5, model="gpt-4", max_tokens=1024)
    class ResponseSchema(BaseModel):
        query: str = Field(..., description="query with brief string")

    question_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", prompt)
        ]
    )
    llm_with_tools = model.with_structured_output(schema=ResponseSchema)
    query_chain = question_prompt | llm_with_tools
    results = query_chain.invoke({'context': inputs})
    return results.query


# Function to fetch icons based on filters
def fetch_icons(color_filter, style_filter, color_palette, iconography, brand_style,
                gradient_usage, imagery, shadow_and_depth, line_thickness, corner_rounding, description,
                icon_color_name=None, icon_style=None):
    f_icons_list = []
    is_above_100_icons = False
    base_url = "https://api.freepik.com/v1/icons"
    headers = {
        "x-freepik-api-key": settings.FREE_PICK_API_KEY
    }
    valid_color = format_value(color_palette) 
    is_valid, matched_color = process_available_color_for_filter(valid_color)
    if is_valid:
        color_filter_value = matched_color.lower()
    else:
        color_filter_value = valid_color
    # attributes with values
    result = process_icons_query(f"{color_palette} {iconography} {brand_style} {gradient_usage} {imagery} {shadow_and_depth} {line_thickness} {corner_rounding}")
    print("result of process_icons_query-->", result)

    if color_filter and style_filter:
        querystring = {"term": description, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": color_filter_value.lower(), "filters[shape]": icon_style}
    elif color_filter:
        querystring = {"term": description, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": color_filter_value.lower()}
    elif style_filter:
        querystring = {"term": description, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[shape]": icon_style, "filters[color]": color_filter_value.lower()}
    else:
        querystring = {"term": description, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": color_filter_value.lower()}

    querystring['order'] = 'relevance'
    # querystring['term'] = 'boxing, gloves, hand, sport, club'
    # Fetch the first batch of 100 icons
    print("Milos querystring in fetch_icons in utils.py")
    print(querystring)
    response = requests.get(base_url, headers=headers, params=querystring)
    json_data = response.json()
    if response.status_code == 200:
        try:
            meta = json_data.get("meta")
            total = meta["pagination"]["total"]
            if total > 100:
                is_above_100_icons = True
        except:
            is_above_100_icons = False

        # Extract Freepik icon data
        for icon in json_data.get('data', []):
            if icon.get('thumbnails'):
                f_icons_list.append({
                    'id': icon.get('id'),
                    'url': icon['thumbnails'][0].get('url')
                })

        if is_above_100_icons:
            querystring['page'] = '2'
            querystring['per_page'] = '50'
            response = requests.get(base_url, headers=headers, params=querystring)
            json_data = response.json()

            for icon in json_data.get('data', []):
                if icon.get('thumbnails'):
                    f_icons_list.append({
                        'id': icon.get('id'),
                        'url': icon['thumbnails'][0].get('url')
                    })
        return f_icons_list, result, None
    else:
        return f_icons_list, result, json_data['invalid_params'][0]['reason']

def format_value(value):
    if value is None:
        return ""
    if value == "None":
        return ""
    return value
