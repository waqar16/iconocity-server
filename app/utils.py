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
import json

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


def process_available_color_for_filter(color: str):
    class ResponseStructure(BaseModel):
        color: Literal[
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
        ] = Field(description="Exact or closest color.")
        is_available: bool = Field(default=False, description="True if color matches or has a close match.")

    template = """
        You are an AI assistant tasked with identifying the exact or closest match from a list of colors Literal.

        Instructions:
          1. If the color provided matches exactly with one of the given colors Literal, return True and the color.
          2. If the color does not match exactly but is close in name or shade to one of the colors Literal, return True and the closest matching color.
          3. If no close match is found, return False and the original color given as input.
    """

    structured_llm = model.with_structured_output(ResponseStructure)
    prompt = ChatPromptTemplate.from_messages([
        ("system", template), 
        MessagesPlaceholder("history", optional=True), 
        ("human", "{question}")
    ])
    partial_prompt = prompt.partial(language='English', query=color)
    chain = partial_prompt | structured_llm

    try:
        response = chain.invoke({"question": color})
        return response.color
    except ValidationError as e:
        # Handle unexpected errors gracefully
        return "gray"  # Default fallback to a valid color
    
   
   
   

# Initialize the fast LLM model
fast_llm = ChatOpenAI(api_key=settings.OPENAI_API_KEY, model="gpt-4", streaming=True)

# Predefined available colors
AVAILABLE_COLORS = [
    'gradient', 'solid-black', 'multicolor', 'blue', 'azure', 'black', 'chartreuse',
    'cyan', 'gray', 'green', 'orange', 'red', 'rose', 'spring-green', 'violet', 'white', 'yellow'
]

def find_closest_color(input_color: str) -> tuple:
    """
    Find the input color's match or closest match from the available color list using OpenAI.
    
    Args:
        input_color (str): The input color name to match.
        
    Returns:
        tuple: (bool, str) - A boolean indicating if the match is exact, and the matching or closest color.
    """
    try:
        # Prompt to check for matching or closest color
        prompt = HumanMessage(content=(
            f"Given the input color '{input_color}', find the most similar color from this list: "
            f"{', '.join(AVAILABLE_COLORS)}. "
            f"Respond with the color that is most similar to '{input_color}' from the list. "
            f"Only provide one color from the list as the response."
        ))

        # Generate a response using OpenAI
        response_stream = fast_llm.stream([prompt])
        
        for message in response_stream:
            matched_color = message.content.strip()
            print(f"Matched color from LLM: {matched_color}")  # Debugging

            # Check if the matched color is in the available colors list
            if matched_color in AVAILABLE_COLORS:
                # Return True for exact match, False for closest match
                is_exact = matched_color.lower() == input_color.lower()
                return (is_exact, matched_color)

            # If exact match isn't found, fallback to Levenshtein distance or other closeness check
            print(f"Exact match not found. Looking for closest match to '{input_color}'")
            closest_color = min(AVAILABLE_COLORS, key=lambda x: levenshtein(x.lower(), input_color.lower()))
            print(f"Closest color determined: {closest_color}")
            return (False, closest_color)

    except Exception as e:
        print(f"Error with OpenAI: {e}")
    
    # Guaranteed fallback if no response or error
    print(f"Fallback response used. Returning default color.")
    return (False, AVAILABLE_COLORS[0])

# Example of Levenshtein distance function for closest match (if needed)
def levenshtein(s1, s2):
    """Compute the Levenshtein distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

    
    
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
    color = format_value(color_palette) 
    if color is None or color == "":
        color_filter_value = color
    else:
        matched_color = find_closest_color(color)
        print("Matched color-->", matched_color)
        color_filter_value = matched_color
        
    color_filter_value = format_value(color_filter_value)
    # attributes with values
    result = process_icons_query(f"{color_palette} {iconography} {brand_style} {gradient_usage} {imagery} {shadow_and_depth} {line_thickness} {corner_rounding}")
    print("result of process_icons_query-->", result)

    if color_filter and style_filter:
        querystring = {"term": description, "slug": imagery, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": color_filter_value[1].lower(), "filters[shape]": icon_style}
    elif color_filter:
        querystring = {"term": description, "slug": imagery, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": color_filter_value[1].lower()}
    elif style_filter:
        querystring = {"term": description, "slug": imagery, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[shape]": icon_style, "filters[color]": color_filter_value[1].lower()}
    else:
        querystring = {"term": description, "slug": imagery, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": color_filter_value[1].lower()}

    querystring['order'] = 'relevance'
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


# Extract and process the data into a user-friendly structure
def extract_figma_summary(figma_response):
    """Extract meaningful data such as artboards, layers, and icons from Figma response."""
    artboards = []
    layers = []
    
    # Process Figma's 'document' field to extract components, layers, or frames
    if figma_response and "document" in figma_response:
        for child in figma_response["document"]["children"]:
            artboards.append({
                "name": child.get("name", "Unnamed"),
                "id": child.get("id", "Unknown"),
                "type": child.get("type", "Unknown")
            })
            # Collect all children layers within artboards
            for layer in child.get("children", []):
                layers.append({
                    "name": layer.get("name", "Unnamed"),
                    "id": layer.get("id", "Unknown"),
                    "type": layer.get("type", "Unknown")
                })
    
    # Return summary data
    return {
        "artboards": artboards,
        "layers": layers
    }
    
    
def extract_design_attributes(figma_response: dict) -> dict:
    """
    Extract design attributes from the provided Figma response JSON using an AI chain-based model.
    Args:
        figma_response (dict): The complete response from the Figma API.
        
    Returns:
        dict: Dictionary of extracted design attributes.
    """

    # Define the prompt for parsing the design attributes
    design_attributes_prompt = """
    Analyze the provided Figma design response JSON to extract the following visual design attributes:
    
    1. **Color Palette**:
        - Identify the primary, accent, and background colors from the design.
        - Report only a single dominant primary color.
        - Indicate the contrast type (e.g., high or low contrast).

    2. **Iconography**:
        - Indicate if icons are present in the design.
        - Report their style (choose one: Flat, Outline, Filled).
        - Report their relative size (choose one: Small, Medium, Large).
        - Report their shape style (choose one: Rounded, Square, Freeform).

    3. **Brand Style**:
        - Determine the brand's overall style from the design (choose one: Corporate, Casual, Modern, Playful).
        - If there are specific industry indicators, return the industry name (e.g., Technology, Healthcare).

    4. **Imagery**:
        - Report the type of imagery in the design (Illustrative, Photorealistic).
        - Report the theme of the imagery (e.g., Technology, Abstract, Nature).

    5. **Gradient Usage**:
        - Check if there are any gradients in the design.
        - If gradients exist, report their type and dominant color stop (Linear, Radial).
        - If no gradients are detected, return "None".

    6. **Shadow and Depth**:
        - Detect if shadows are being used.
        - Report the type of shadows (e.g., Drop shadows, Inner shadows, None).
        - Determine if they give an elevated effect or flat effect.

    7. **Line Thickness**:
        - Report if the lines in the design are consistent or variable (choose one: Thick, Thin, Variable).

    8. **Corner Rounding**:
        - Identify if elements have rounded corners and the degree (choose one: Sharp corners, Slightly rounded, Fully rounded).

    9. **Description**:
        - Generate a concise description of the design using up to 10 nouns that best describe the design's content.

    JSON Input Provided:
    {figma_response}
    
    Output Format:
    Provide the extracted attributes in the following JSON format:
    {{
        "color_palette": "blue",
        "iconography": "Flat, Medium, Rounded",
        "brand_style": "Corporate",
        "gradient_usage": "Linear, Blue-Yellow",
        "shadow_and_depth": "Drop shadows, Elevated",
        "line_thickness": "Thin",
        "corner_rounding": "Slightly rounded",
        "imagery": "Illustrative, Technology",
        "description": "boxing, gloves, club, website, training, excellence, athletes, sport, youth, sessions"
    }}
    Ensure responses are short and directly related to the design context.
    """

    # Chain model placeholder logic
    @chain
    def parse_figma_response(inputs: dict):
        """
        Send the prompt and the Figma response to the AI chain and process the output.
        Args:
            inputs (dict): Input dictionary containing Figma response and AI prompt.
        Returns:
            dict: AI's parsed response.
        """
        response = model.invoke(
            [HumanMessage(
                content=[
                    {"type": "text", "text": inputs["prompt"]},
                    {"type": "json", "json": inputs["figma_response"]}
                ]
            )]
        )
        
        print("Model Response:")
        print(response.content)  # Log AI response
        return response.content

    # Transform Chain for input processing
    transform_figma_chain = TransformChain(
        input_variables=["figma_response"],
        output_variables=["response"],
        transform=lambda x: {"figma_response": json.dumps(figma_response)}  # Ensure JSON is properly formatted
    )

    # Full AI response chain combining input + prompt
    ai_chain = transform_figma_chain | parse_figma_response

    # Call the AI chain
    result = ai_chain.invoke({"figma_response": figma_response, "prompt": design_attributes_prompt})

    # Convert the AI response string to JSON (error-safe)
    try:
        extracted_attributes = json.loads(result)
    except json.JSONDecodeError:
        extracted_attributes = {"error": "AI response could not be parsed"}
    
    # Return extracted attributes
    return extracted_attributes