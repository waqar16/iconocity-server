from langchain_core.pydantic_v1 import BaseModel, Field
from langchain.chains import TransformChain
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.runnables import chain
from langchain_core.output_parsers import JsonOutputParser
import webcolors

class ImageInformation(BaseModel):
    color_palette: str = Field(description="The color palette of the picture")
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
    
    2. Iconography:
    • Check if the design includes any icons.
    • Identify the style of the icons (choose one: Flat, Outline, Filled).
    • Observe the relative size of the icons (choose one: Small, Medium, Large).
    • Describe the shape of the icons (choose one: Rounded, Square, Freeform).
    
    3.Brand Style:
    • Determine the overall style and tone of the design. Categorize it as one of the following:
        • Corporate: Formal, professional, typically used for business or financial services.
        • Casual: Friendly, relaxed, often seen in lifestyle or personal brand designs.
        • Modern: Minimalistic, clean, often characterized by simplicity and elegance.
        • Playful: Vibrant, fun, colorful, often used for children's products or entertainment brands.
        • If the design represents a specific industry or niche, choose an appropriate label (e.g., Construction, \
        Education, Healthcare).

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
        model = ChatOpenAI(
            temperature=0.5, model="gpt-4-vision-preview", max_tokens=1024)
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
    list = [
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
    if color in list:
        return True, color
    return False, color
