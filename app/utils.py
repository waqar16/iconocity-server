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
    # vision_prompt = """Instruction:
    # Analyze the design to extract specific visual attributes. 
    # Review the design carefully and identify the following 
    # attributes:
    
    # 1.Color Palette:
    # • Identify the color used in the design.
    # • Determine the accent color that complements the primary palette.
    # • Note the background color.
    # • Assess the contrast level (high contrast vs. low contrast).
    # • Get Major color only, and it should be only one color name

    # 2. Iconography:
    # • Check if the design includes any icons.
    # • Identify the style of the icons (choose one: Flat, Outline, Filled).
    # • Observe the relative size of the icons (choose one: Small, Medium, Large).
    # • Describe the shape of the icons (choose one: Rounded, Square, Freeform).

    # 3.Brand Style:
    # • Determine the overall style and tone of the design.
    #     Categorize it as one of the following:
    #     • Corporate: Formal, professional, typically used for business or financial services.
    #     • Casual: Friendly, relaxed, often seen in lifestyle or personal brand designs.
    #     • Modern: Minimalistic, clean, often characterized by simplicity and elegance.
    #     • Playful: Vibrant, fun, colorful, often used for children’s products or entertainment brands.
    #     If the design represents a specific industry (e.g., healthcare, technology, education), specify that \
    #     industry as the brand style** (e.g., "Healthcare," "Technology," "Education"). Identify the industry based \
    #     on any specific visual cues, symbols, or elements related to that field (e.g., stethoscopes for healthcare, \
    #     computers for technology).


    # 4. Imagery:
    # • Note the style of imagery used (choose one: Illustrative, Photorealistic).
    # • Identify the theme of the imagery (choose one: Nature, Technology, Abstract).

    # 5. Gradient Usage:
    # • Detect the presence of gradients in the design.
    # • If gradients are present, identify the direction (choose one: Linear, Radial) and the dominant gradient color stop.
    # • If no gradients are present, label this as "None".

    # 6. Shadow and Depth:
    # • Check for the use of shadows (choose one: Drop shadows, Inner shadows, None).
    # • Determine the depth effect created by these shadows (choose one: Flat, Elevated).

    # 7. Line Thickness:
    # • Assess the consistency of line weight throughout the design (choose one: Thick, Thin, Variable).

    # 8. Corner Rounding:
    # •  Identify the degree of corner rounding in shapes (choose one: Sharp corners, Slightly rounded, Fully rounded).

    # 9. Description:
    # •  Description should contain up to 10 nouns that best describe the content. Rank the nouns for description according to how well they describe the picture. Give description as single string with list of up to 10 nouns separated by comma, without numbering and new line. Ensure the nouns cover both direct and related concepts to capture a wide variety of possible icons.
    # •  If the design represents a specific website page or app screen, include relevant keywords (e.g., "homepage," "profile," "dashboard," "settings").

    
    # Output:
    # • For each of the above attributes, populate the results as a single keyword representing the attribute detected. \
    # Avoid using non-descriptive answers like "Yes" or "No"; instead, specify relevant details or use "None" where \
    # applicable.
    # Example Output:
    #     • Color Palette: Blue, Yellow, White, Gradient, Rainbow
    #     • Iconography: Flat, Medium, Rounded
    #     • Brand Style: Corporate
    #     • Imagery: Illustrative, Technology
    #     • Gradient Usage: Linear, Blue-Yellow
    #     • Shadow and Depth: Drop shadows, Elevated
    #     • Line Thickness: Thin
    #     • Corner Rounding: Slightly rounded
    #     • Description: boxing, gloves, club, website, training, excellence, athletes, sport, youth, sessions"""

    vision_prompt = """Instruction:
    Analyze the Figma design to extract detailed visual and contextual attributes. 
    Review the design carefully and identify the following elements:

    1. **Color Palette**:
    • Identify the primary color used in the design.
    • Determine the accent color that complements the primary palette.
    • Assess the contrast level (e.g., high contrast, low contrast).
    • Provide only one major color.

    2. **Iconography**:
    • Identify if the design includes any icons.
    • Describe the style of the icons (choose one: Flat, Outline, Filled, Minimalist).
    • Specify the relative size of the icons (choose one: Small, Medium, Large).
    • Describe the shape of the icons (choose one: Rounded, Square, Freeform).

    3. **Brand Style**:
    • Define the overall style and tone of the design. Categorize it as one of the following:
        • Corporate: Formal, professional, business-oriented.
        • Casual: Relaxed, friendly, lifestyle-oriented.
        • Modern: Minimalistic, clean, simple.
        • Playful: Fun, colorful, energetic.
    • Identify Freepik-compatible styles (e.g., Minimalist, Flat, Outlined).
    • If the design belongs to a specific industry (e.g., healthcare, technology), specify the industry based on any related symbols or elements (e.g., stethoscopes for healthcare, computers for technology).

    4. **Imagery & Illustrations**:
    • Identify the style of imagery used (choose: UI Icons).
    • Determine the theme of the imagery (choose one: Nature, Technology, Abstract, etc.).

    5. **Gradient Usage**:
    • Detect the presence of gradients in the design.
    • If gradients are used, specify the direction (Linear, Radial) and the dominant gradient color.
    • If no gradients are present, label as "None".

    6. **Shadow and Depth**:
    • Determine the use of shadows (choose one: Drop shadows, Inner shadows, None).
    • Specify the depth effect (choose one: Flat, Elevated).

    7. **Line Thickness & Stroke**:
    • Assess the consistency of line thickness throughout the design (choose one: Thick, Thin, Variable).

    8. **Corner Rounding**:
    • Identify the degree of corner rounding (choose one: Sharp, Slightly Rounded, Fully Rounded).

    9. **Keyword-Based Content Filtering**:
    • Generate up to 4 most relevant nouns that best describe the content of the design.
    • Rank the keywords based on relevance.
    • Exclude seasonal or unrelated themes (e.g., avoid "Christmas" unless explicitly relevant).
    • Example: "fitness, health, tracking, gym"

    10. **Contextual Understanding**:
    • Consider the context of the design (e.g., is it for a fitness app, medical app, or social network?).
    • Identify specific functionality that might require a variety of icons, such as icons for tracking, navigation, or social interactions.
    • Ensure icons match the intended use case while filtering out irrelevant themes.

    Output:
    For each of the above attributes, provide specific, relevant details. Avoid vague or non-descriptive answers. The results should reflect diverse and varied aspects of the design, ensuring alignment with Freepik's style filters and intended user context.
    Example Output:
        • Color Palette: Blue, Yellow, White, Gradient, Rainbow
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
        prompt = HumanMessage(content=(
            f"Given the input color '{input_color}', find the most similar color from this list: "
            f"{', '.join(AVAILABLE_COLORS)}. "
            f"Respond with the color that is most similar to '{input_color}' from the list. "
            f"Only provide one color from the {len(AVAILABLE_COLORS)} options of {AVAILABLE_COLORS}."
            f"These are the examples: If the input color is 'golden', the response should be 'yellow', 'pink' -> 'rose', purple -> 'violet'. and so on."
        ))

        response_stream = fast_llm.stream([prompt])

        matched_color = None
        for message in response_stream:
            response_content = message.content.strip()
            if response_content:  # Only process non-empty responses
                # Validate the matched color
                if response_content in AVAILABLE_COLORS:
                    matched_color = response_content
                    is_exact = matched_color.lower() == input_color.lower()
                    return (is_exact, matched_color)

        # If no valid match from LLM, fallback to closest match
        print(f"No valid match found in LLM response. Finding closest match for '{input_color}'.")
        closest_color = find_closest_color_fallback(input_color)
        return (False, closest_color)

    except Exception as e:
        print(f"Error during OpenAI processing: {e}")

    # Guaranteed fallback
    print(f"Returning default fallback color.")
    return (False, AVAILABLE_COLORS[0])


def find_closest_color_fallback(input_color: str) -> str:
    """
    Fallback mechanism to find the closest color using Levenshtein distance.

    Args:
        input_color (str): The input color name to match.

    Returns:
        str: The closest color from the available color list.
    """
    try:
        # Use Levenshtein distance to find the closest match
        closest_color = min(AVAILABLE_COLORS, key=lambda x: levenshtein(x.lower(), input_color.lower()))
        print(f"Closest color via fallback: {closest_color}")
        return closest_color
    except Exception as e:
        print(f"Error in fallback mechanism: {e}")
        # Fallback to the first available color in case of error
        return AVAILABLE_COLORS[0]


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

    # if not color_filter and not style_filter:
    #     description = format_value(imagery)

    # Process icon color name if provided
    if icon_color_name or not "None":
        color_filter_value = icon_color_name
        print("Using provided icon_color_name:", color_filter_value)
    else:
        # Fallback to color_palette
        color = format_value(color_palette)
        if color.lower() not in AVAILABLE_COLORS:
            matched_color = find_closest_color(color)
            print("Matched color from color_palette:", matched_color[1])
            color_filter_value = matched_color[1]
        else:
            color_filter_value = color

    color_filter_value = format_value(color_filter_value)
    print("color_filter_value-->", color_filter_value)

    # Process attributes and query icons
    result = process_icons_query(
        f"{color_filter_value} {iconography} {brand_style} {gradient_usage} {imagery} {shadow_and_depth} "
        f"{line_thickness} {corner_rounding}"
    )
    # print("Result of process_icons_query-->", result)

    # description_terms = " ".join(description.split(","))
    description += " minimalist, UI icon"

    # Construct querystring based on provided filters
    querystring = {
        "term": f"{description}, {color_filter_value if color_filter_value else ''} {icon_style if icon_style else ''}, {imagery}",
        "thumbnail_size": "256", 
        "per_page": "100",  # Ensure only 150 icons are fetched
        "page": "1",       # Fetch the first page
        "order": 'relevance'
    }

    # Only include filters if they have valid values
    if color_filter_value:
        querystring["filters[color]"] = color_filter_value.lower()
    if icon_style:  # Only include shape filter if icon_style is provided
        querystring["filters[shape]"] = icon_style
    if style_filter:  # Only include style filter if it's True
        querystring["filters[style]"] = style_filter

    # Fetch the first batch of 100 icons
    print("Milos querystring in fetch_icons in utils.py")
    print(querystring)
    response = requests.get(base_url, headers=headers, params=querystring)
    print(response)
    json_data = response.json()

    if response.status_code != 200:
        return f_icons_list, result, "Something Wrong with the FreePik API"
    if response.status_code == 200:
        try:
            print("Response-->", json_data)
            meta = json_data.get("meta")
            per_page = meta["pagination"]["per_page"]
            total = meta["pagination"]["total"]
            print("Total Icons-->", per_page)
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
        return f_icons_list, result, "Something Wrong with the FreePik API"


def format_value(value):
    if value is None:
        return ""
    if value == "None":
        return ""
    return value
