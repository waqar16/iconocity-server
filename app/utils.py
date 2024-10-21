from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains import TransformChain
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from django.conf import settings
import requests

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
        • Corner Rounding: Slightly rounded"""


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
        return msg.content

    load_image_chain = TransformChain(
        input_variables=["image"],
        output_variables=["image"],
        transform=lambda x: {"image": image_base64}
    )

    vision_chain = load_image_chain | image_model | parser
    return vision_chain.invoke({'image': image_base64, 'prompt': vision_prompt})


def custom_error_message(errors):
    for key, value in errors.items():
        if isinstance(value, list):
            return {'error': value[0].replace('field', key + ' field')}
        elif isinstance(value, dict):
            return custom_error_message(value)
    return {'error': 'Unknown error'}


def Color_Available_in_Filter(color):
    Valid_Filter_list_FREEPIK = [
        'blue',
        'black',
        'cyan',
        'chartreuse',
        'azure',
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
        color: str = Field(default="", description="Color name detected from input")
        is_available: bool = Field(default=False, description="Whether or not the color is available")
    template = """
        You are an AI assistant tasked with identifying the closest match from a list of available colors.
    Available Colors:
        Blue
        Black
        Cyan
        Chartreuse
        Azure
        Gray
        Green
        Orange
        Red
        Rose
        Spring-Green
        Violet
        White
        Yellow
        
        Instructions:
          If the color provided does not match any of the available colors, return the original color given as input.
          If the given input color matches one of the available colors, return True and the color; otherwise,
          return False and the original color.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", template),
            MessagesPlaceholder("history", optional=True), ("human", "{question}")
        ]
    )

    partial_prompt = prompt.partial(language='English', query=color)
    chain = partial_prompt | model | ResponseStructure
    response = chain.invoke({"history": [], "question": color})
    return response

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

    model = ChatOpenAI(temperature=0.5, model="gpt-4-vision-preview", max_tokens=1024)
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
                gradient_usage, imagery, shadow_and_depth, line_thickness, corner_rounding,
                icon_color_name=None, icon_style=None):
    f_icons_list = []
    is_above_100_icons = False
    base_url = "https://api.freepik.com/v1/icons"
    headers = {
        "x-freepik-api-key": settings.FREE_PICK_API_KEY
    }
    # attributes with values
    result = process_icons_query(f"{color_palette} {iconography} {brand_style} {gradient_usage} {imagery} {shadow_and_depth} {line_thickness} {corner_rounding}")

    if color_filter and style_filter:
        querystring = {"term": result, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": icon_color_name.lower(), "filters[shape]": icon_style}
    elif color_filter:
        querystring = {"term": result, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": icon_color_name.lower()}
    elif style_filter:
        querystring = {"term": result, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[shape]": icon_style, "filters[color]": color_palette}
    else:
        querystring = {"term": result, "thumbnail_size": "256", "per_page": "100", "page": "1",
                       "filters[color]": color_palette}

    querystring['order'] = 'relevance'

    # Fetch the first batch of 100 icons
    response = requests.get(base_url, headers=headers, params=querystring)
    json_data = response.json()
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
    return f_icons_list, result

def format_value(value):
    if value is None:
        return ""
    if value == "None":
        return ""
    return value
