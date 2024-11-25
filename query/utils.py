import os
from typing import Literal

from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
from django.conf import settings
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

os.environ["OPENAI_API_KEY"]= settings.OPENAI_API_KEY
llm = ChatOpenAI(model="gpt-4o-mini")

def GeneralQueryAnswer(message, icon_attributes):
    class Output_Structure(BaseModel):
        color_palette: str = Field(description="The color palette of the picture")
        iconography: str = Field(description="The iconography of the picture")
        brand_style: str = Field(description="The band style of the picture")
        gradient_usage: str = Field(description="The gradient usage of the picture")
        imagery: str = Field(description="The imagery of the picture")
        shadow_and_depth: str = Field(description="The shadow and depth of the picture")
        line_thickness: str = Field(description="The line thickness of the picture")
        corner_rounding: str = Field(description="The corner rounding of the picture")
        general_response: str = Field(default=None, description="General response of the input query")


    structured_llm = llm.with_structured_output(Output_Structure)
    sys_prompt = """
    You are a highly skilled AI designer specializing in refining icon design based on user instructions. 
    Below are the current design settings for the icon. Based on the user's query, you will adjust these settings 
    and provide an updated design description.

    ### Current Icon Design Settings:
    • **Color Palette:** {color_palette}
    • **Iconography:** {iconography}
    • **Brand Style:** {brand_style}
    • **Imagery:** {imagery}
    • **Gradient Effect:** {gradient_usage}
    • **Shadow and Depth:** {shadow_and_depth}
    • **Line Thickness:** {line_thickness}
    • **Corner Rounding:** {corner_rounding}

    ### User Input Guidelines:
    The user might:
    1. Suggest specific changes (e.g., "Make the icon rounded with softer colors").
    2. Ask for a theme-based design update (e.g., "Design for love" or "Corporate style").
    3. Use abstract queries (e.g., "Make it playful" or "Modern look").
    4. Submit an unclear or invalid query (e.g., incomplete, ambiguous, or unrelated instructions).

    ### Task Instructions:
    - **For Clear and Valid Queries:** Update the attributes as per the user's instructions.
    - **For Industry or Theme-Related Queries:** If the query suggests a theme such as "banking," "finance," "mobile app," etc., update:
        - **Brand Style:** Adjust to fit industry norms (e.g., "Corporate," "Techy," "Professional").
        - **Imagery:** Adjust to reflect the industry (e.g., "Building," "Graph," "Abstract").
        - **Color Palette:** Choose colors that fit the industry (e.g., "Blue" for Finance, "Green" for Growth).
    - **For Ambiguous or Invalid Queries:** 
        - Retain all current design settings unchanged.
        - Use the `general_response` field to guide the user on what is unclear or missing.
        - Provide specific suggestions on how to refine their query.

    ### Output Requirements:
    For each attribute, provide precise keywords representing the updated design setting. Use clear, descriptive answers 
    (e.g., "Warm Red-Pink", "Flat and Minimalistic"). If no change is needed, retain the current value.

    ### Example Query and Output:

    **Query:** "banking"
    **Output:**
    - Color Palette: Blue
    - Iconography: Minimalistic, Professional
    - Brand Style: Corporate
    - Imagery: Building, Graph
    - Gradient Usage: Subtle Gradient
    - Shadow and Depth: Medium Shadows
    - Line Thickness: Medium
    - Corner Rounding: Slightly Rounded
    - General Response: Updated design to reflect a banking theme.

    **Query:** "finance"
    **Output:**
    - Color Palette: Green, Blue
    - Iconography: Simple, Abstract
    - Brand Style: Professional, Corporate
    - Imagery: Graph, Money, Stability
    - Gradient Usage: Soft Gradient
    - Shadow and Depth: Subtle Shadows
    - Line Thickness: Thin
    - Corner Rounding: None
    - General Response: Updated design to reflect a finance theme.

    **Query:** "mobile application"
    **Output:**
    - Color Palette: Cool Blues, Vibrant Accents
    - Iconography: Rounded, Minimalist
    - Brand Style: Modern, Techy
    - Imagery: Mobile, App Icon, Clean Lines
    - Gradient Usage: Smooth Gradient
    - Shadow and Depth: Soft Shadows
    - Line Thickness: Thin
    - Corner Rounding: Fully Rounded
    - General Response: Updated design to fit the mobile application theme.

    **Query:** "escrow service"
    **Output:**
    - Color Palette: Blue, Neutral Tones
    - Iconography: Secure, Trustworthy
    - Brand Style: Professional, Corporate
    - Imagery: Shield, Contract, Security
    - Gradient Usage: Soft Gradient
    - Shadow and Depth: Medium Shadows
    - Line Thickness: Medium
    - Corner Rounding: Slightly Rounded
    - General Response: Updated design to reflect an escrow service theme.

    **Query:** "Change it!"
    **Output:**
    Keep everything the same. General Response: Request is unclear. Please specify which attributes you'd like to change (e.g., color, style, or theme).
    """
    # sys_prompt = """You are interacting with an AI that helps you change the design of an icon. Below are the current \
    # design settings of the icon. You can adjust them by giving simple instructions.
    
    # Current Icon Design Settings:
    # • Color Palette: {color_palette}
    # • Iconography: {iconography}
    # • Brand Style: {brand_style}
    # • Imagery: {imagery}
    # • Gradient Effect: {gradient_usage}
    # • Shadow and Depth: {imagery}
    # • Line Thickness: {line_thickness}
    # • Corner Rounding: {corner_rounding}
    
    # User Input Guidelines:
    #     You can change any of the following icon design settings:
    #         Color Palette (e.g., color).
    #         Iconography (e.g., flat, outlined, filled; also change the size and shape of the icon).
    #         Brand Style(e.g., corporate, casual, modern, playful).
    #         Imagery (e.g., style and theme of any images or graphics).
    #         Gradient Usage (e.g., add or remove gradient effects).
    #         Shadow and Depth (e.g., adjust shadow effects to make the icon look flat or elevated).
    #         Imagery (e.g., style and theme of any images or graphics).
    #         Line Thickness (e.g., make lines thicker, thinner, or variable).
    #         Corner Rounding (e.g., make the icon’s corners sharper or more rounded).
    
    # Output:
    # • For each of the above attributes, populate the results as a single keyword representing the attribute detected. \
    # Avoid using non-descriptive answers like "Yes" or "No"; instead, specify relevant details or use "None" where \
    # applicable.
    # Example Output:
    #     • Color Palette: Blue, High Contrast
    #     • Iconography: Flat, Medium, Rounded
    #     • Brand Style: Corporate
    #     • Imagery: Illustrative, Technology
    #     • Gradient Usage: Linear, Blue-Yellow
    #     • Shadow and Depth: Drop shadows, Elevated
    #     • Line Thickness: Thin
    #     • Corner Rounding: Slightly rounded
        
    # Note: Always set the `general_response` of input query if any icon design settings changed.
    # """


    prompt = ChatPromptTemplate.from_messages([("system", sys_prompt), MessagesPlaceholder("history", optional=True), ("human", "{question}")])
    partial_prompt = prompt.partial(
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


def IdentifyQuery(query):

    class Output_Structure(BaseModel):
        color: str = Field(default=None, description="Color name detected from input query")
        shape: str = Field(default=None, description="Shape name detected from input query")
        path: Literal['color', 'shape', 'general'] = Field(description="general query from input query")
        

    if not query or query.strip() == "":
        return {"error": "Query cannot be empty or None"}


    structured_llm = llm.with_structured_output(Output_Structure)
    # sys_prompt = """
    #     You are an AI designed to classify queries based on their content, specifically detecting colors, shapes, or general topics. 
    #     For each query, determine if it is related to color, shape, or a general topic, and respond with the appropriate classification.
    #     Ensure the shape attribute, if detected, is restricted to one of the following choices: outline, fill, lineal-color, hand-drawn.
    # """
    sys_prompt = """
        You are an AI designed to classify queries based on their content, specifically detecting colors, shapes, or general topics. 
        For each query, determine if it is related to color, shape, or a general topic, and respond with the appropriate classification.
        Ensure the shape attribute, if detected, is restricted to one of the following choices: outline, fill, lineal-color, hand-drawn.
        
        Instructions:
        1. If the query mentions only a color or shape, classify it accordingly.
        2. If the query contains a combination of color or shape along with general words (e.g., "theme", "view", "style"), classify it as a general query.
        3. Return the corresponding path ("color", "shape", "general") based on the classification.
        4. For general queries that combine descriptive terms with colors or shapes (e.g., "red lava theme", "black mountain view"), return "general" and classify the elements accordingly.
        5. If no clear color or shape is found but general descriptive words are present, return "general".
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", sys_prompt),
            MessagesPlaceholder("history", optional=True), ("human", "{question}")
        ]
    )
    chain = prompt | structured_llm
    response = chain.invoke({"history": [], "question": query})
    # Ensure expected attributes exist in response before accessing them
    if 'color' in response and response['color']:
        response['color'] = response['color'].lower()  # Safely call lower() if color exists

    if 'shape' in response and response['shape']:
        response['shape'] = response['shape'].lower()  # Safely call lower() if shape exists
    return response


def changeIconColorAndShapeQueryBot(query):

    class Output_Structure(BaseModel):
        color: str = Field(default=None, description="Color name detected from input query")
        shape: str = Field(default=None, description="Shape name detected from input query")
        isRelatedColor: bool = Field(default=False, description="if query is related to available color return True, else return False")
        isRelatedShape: bool = Field(default=False, description="if query is related to available shape return True, else return False")
        general_response: str = Field(default=None, description="General response of the input query")
    

    structured_llm = llm.with_structured_output(Output_Structure)
    sys_prompt = """You are interacting with an AI that helps you change the design of an icon. Below are the current \
        design settings of the icon. You can adjust them by giving simple instructions, like "make the icon color blue" \
        or "make the icon bigger."

        Output:
        • For each of the above attributes, populate the results as a single keyword representing the attribute detected. \
        Avoid using non-descriptive answers like "Yes" or "No"; instead, specify relevant details or use "None" where \
        applicable.
        
        OUTPUT SHAPE:
        Find closet or exact match [outline, fill, lineal-color, hand-drawn] output shape should be in outline, fill, lineal-color, hand-drawn.
        
        OUTPUT COLOR:
        Find closet or exact match [gradient, solid-black, multicolor, azure, black, blue, chartreuse,
         cyan, gray, green, orange, red, rose, spring-green, violet, white, yellow]

        isRelatedColor:
            Set this to True if the color in the input matches any items on the lists.
            Set this to False if the detected color is an approximation or not an exact match.

        isRelatedShape:
            Set this to True if the shape in the input matches any items on the lists.
            Set this to False if the detected shape is an approximation or not an exact match.

        Instructions:
            1. When there is an exact match for both color and shape:
                - Return the corresponding keywords and set `isRelatedColor` and `isRelatedShape` to True.
                - Set the `general_response` to:
                    if `isRelatedColor` is True :
                  'The icon color has been updated to color',
                    if `isRelatedShape` is True :
                   'The shape has been updated to shape.'
                if both `isRelatedColor` and `isRelatedShape`:
                'The icon color has been updated to color, and the shape has been updated to shape.'
            2. When there is a match for either color or shape but not both:
                - Return the exact match for one attribute and the closest match for the other.
                - Set `isRelatedColor` or `isRelatedShape` to True for exact matches, and False for approximate matches.
                - Set the `general_response` to:
                  'The icon color has been updated to color, and the shape has been updated to shape (if shape is None skip this line: the shape has been updated to shape).' (mention both the exact and closest matches).
            3. If the query is unrelated to color or shape, respond with:
                'I’m here to assist you with customizing the color and shape of the icons. Let me know how you'd like to adjust them.'
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