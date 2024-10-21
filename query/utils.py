import os
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

os.environ["OPENAI_API_KEY"]= settings.OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4o-mini")

def ChangeIconQueryBot(message, icon_attributes, language):
    class Output_Structure(BaseModel):
        response: str = Field(
            description=f"Resolve user query in {language} in Escape Sequences")
        # )
        isRelated: bool = Field(description="if query is related to design setting icon return True, else return False")
        color_palette: str = Field(description="The color palette of the picture")
        iconography: str = Field(description="The iconography of the picture")
        brand_style: str = Field(description="The band style of the picture")
        gradient_usage: str = Field(description="The gradient usage of the picture")
        imagery: str = Field(description="The imagery of the picture")
        shadow_and_depth: str = Field(description="The shadow and depth of the picture")
        line_thickness: str = Field(description="The line thickness of the picture")
        corner_rounding: str = Field(description="The corner rounding of the picture")


    structured_llm = llm.with_structured_output(Output_Structure)
    sys_prompt = """You are interacting with an AI that helps you change the design of an icon. Below are the current \
    design settings of the icon. You can adjust them by giving simple instructions, like "make the icon color blue" \
    or "make the icon bigger."
    
    Current Icon Design Settings:
    • Color Palette: {color_palette}
    • Iconography: {iconography}
    • Brand Style: {brand_style}
    • Imagery: {imagery}
    • Gradient Effect: {gradient_usage}
    • Shadow and Depth: {imagery}
    • Line Thickness: {line_thickness}
    • Corner Rounding: {corner_rounding}
    
    User Input Guidelines:
        You can change any of the following icon design settings:
            Color Palette (e.g., color, or contrast level).
            Iconography (e.g., flat, outlined, filled; also change the size and shape of the icon).
            Brand Style(e.g., corporate, casual, modern, playful).
            Imagery (e.g., style and theme of any images or graphics).
            Gradient Usage (e.g., add or remove gradient effects).
            Shadow and Depth (e.g., adjust shadow effects to make the icon look flat or elevated).
            Imagery (e.g., style and theme of any images or graphics).
            Line Thickness (e.g., make lines thicker, thinner, or variable).
            Corner Rounding (e.g., make the icon’s corners sharper or more rounded).
    
    Output:
    • For each of the above attributes, populate the results as a single keyword representing the attribute detected. \
    Avoid using non-descriptive answers like "Yes" or "No"; instead, specify relevant details or use "None" where \
    applicable.
    Example Output:
        • Color Palette: Blue, High Contrast
        • Iconography: Flat, Medium, Rounded
        • Brand Style: Corporate
        • Imagery: Illustrative, Technology
        • Gradient Usage: Linear, Blue-Yellow
        • Shadow and Depth: Drop shadows, Elevated
        • Line Thickness: Thin
        • Corner Rounding: Slightly rounded"""


    prompt = ChatPromptTemplate.from_messages([("system", sys_prompt), MessagesPlaceholder("history", optional=True), ("human", "{question}")])
    partial_prompt = prompt.partial(
                        language=language,
                        color_palette=icon_attributes.get("color_palette", " "),
                        iconography=icon_attributes.get("iconography", " "),
                        brand_style=icon_attributes.get("brand_style", " "),
                        gradient_usage=icon_attributes.get("gradient_usage", " "),
                        imagery=icon_attributes.get("imagery", " "),
                        shadow_and_depth=icon_attributes.get("shadow_and_depth", " "),
                        line_thickness=icon_attributes.get("line_thickness", " "),
                        corner_rounding=icon_attributes.get("corner_rounding", " "),
    )

    chain = partial_prompt | structured_llm
    response = chain.invoke({"history": [], "question": message})
    return response


def changeIconColorAndShapeQueryBot(query):

    class Output_Structure(BaseModel):
        color: str = Field(default=None, description="Color name detected from input query")
        shape: str = Field(default=None, description="Shape name detected from input query")
        isRelatedColor: bool = Field(default=False, description="if query is related to available color return True, else return False")
        isRelatedShape: bool = Field(default=False, description="if query is related to available shape return True, else return False")
        general_response: str = Field(default=None, description="General response of the input query")
        
        color_palette: str = Field(default=None, description="The iconography of the picture")
        iconography: str = Field(default=None, description="The iconography of the picture")
        brand_style: str = Field(default=None, description="The band style of the picture")
        gradient_usage: str = Field(default=None, description="The gradient usage of the picture")
        imagery: str = Field(default=None, description="The imagery of the picture")
        shadow_and_depth: str = Field(default=None, description="The shadow and depth of the picture")
        line_thickness: str = Field(default=None, description="The line thickness of the picture")
        corner_rounding: str = Field(default=None, description="The corner rounding of the picture")


    structured_llm = llm.with_structured_output(Output_Structure)
    sys_prompt = """
    You are an AI assistant designed to identify colors and shapes from an input query. You will use the predefined 
    lists of colors and shapes provided below. If the input query does not exactly match any of the available options,
    you must determine and return the closest possible match from the lists.
    Note: If the input query does not match any color or shape, respond by offering assistance with changing the color
    and design of the icon. Let the user know you're here to help with customizing the icon's color and shape."
    
    Guidelines:
        You can change any of the following icon design settings:
            •   Color Palette (e.g., color, or contrast level).
            •   Iconography (e.g., flat, outlined, filled; also change the size and shape of the icon).
            •   Brand Style(e.g., corporate, casual, modern, playful).
            •   Imagery (e.g., style and theme of any images or graphics).
            •   Gradient Usage (e.g., add or remove gradient effects).
            •   Shadow and Depth (e.g., adjust shadow effects to make the icon look flat or elevated).
            •   Imagery (e.g., style and theme of any images or graphics).
            •   Line Thickness (e.g., make lines thicker, thinner, or variable).
            •   Corner Rounding (e.g., make the icon’s corners sharper or more rounded).
        
        Output:
            • Color Palette: Blue, High Contrast
            • Iconography: Flat, Medium, Rounded
            • Brand Style: Corporate
            • Imagery: Illustrative, Technology
            • Gradient Usage: Linear, Blue-Yellow
            • Shadow and Depth: Drop shadows, Elevated
            • Imagery: Illustrative, Technology
            • Line Thickness: Thin
            • Corner Rounding: Slightly rounded

    Available Colors:
        •  Blue
        •  Black
        •  Cyan
        •  Chartreuse
        •  Azure
        •  Gray
        •  Green
        •  Orange
        •  Red
        •  Rose
        •  Spring-Green
        •  Violet
        •  White
        •  Yellow
        
    Available Shapes:
        •  Outline
        •  Fill
        •  Linear Shape
        •  Hand Drawn
    Output Requirements:
        Detected Color: Return the closest color from the available list.
        Detected Shape: Return the closest shape from the available list.
    isRelatedColor:
        Set this to True if the color in the input match any items on the lists.
        Set this to False if the detected color is an approximation or not an exact match.
    isRelatedShape:
        Set this to True if the shape in the input match any items on the lists.
        Set this to False if the detected shape is an approximation or not an exact match.
        
    Instructions:
        When there is an exact match for both color and shape, return the corresponding keywords and set
         `isRelatedShape`, `isRelatedColor` to True.
        When the match is not exact, return the closest color and shape, and set `isRelatedColor` and `isRelatedShape`
        to False.
        If no color and shape if found then set answer in `general_response`.
        
        For each of the above guideline attributes, populate the results as a single keyword representing the attribute 
        detected. Avoid using non-descriptive answers like "Yes" or "No"; instead, specify relevant details or use 
        "None" where applicable.
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", sys_prompt),
            MessagesPlaceholder("history", optional=True), ("human", "{question}")
        ]
    )
    partial_prompt = prompt.partial(language='English', query=query)
    chain = partial_prompt | structured_llm
    response = chain.invoke({"history": [], "question": query})
    return response