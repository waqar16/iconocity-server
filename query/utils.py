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
        description: str = Field(description="Description used as a keyword for the icons")
        style: str = Field(description="The style of the icon")
        general_response: str = Field(default=None, description="General response of the input query")

    # def refine_description(message: str, current_description: str) -> str:
    #     """
    #     Refines the description field based on the user's query. 
    #     If the query contains the genral word like "bull", "Make it Bike icons" it extracts relevant keywords; otherwise, it retains the current description.
    #     """
    #     keywords = [word.lower() for word in message.split()]
    #     if "icons" in keywords:
    #         return " ".join(keywords).replace("icons", "").strip()
    #     return current_description

    # new_description = refine_description(message, icon_attributes.get("description", ""))
    # description_updated = new_description != icon_attributes.get("description", "")

    # # Update description and adjust general response if changed
    # icon_attributes["description"] = new_description
    # if description_updated:
    #     icon_attributes["general_response"] = f"The design has been updated to match your query for '{new_description}' icons. The settings are now focused on this theme. Let me know if you'd like further adjustments."

    structured_llm = llm.with_structured_output(Output_Structure)

    sys_prompt = """
   You are an AI expert in refining icon designs based on user inputs. Using the current design settings provided below, analyze the user's query and adjust the settings as required.  

### **Current Icon Design Settings:**  
- **Color Palette:** {color_palette}  
- **Iconography:** {iconography}  
- **Brand Style:** {brand_style}  
- **Imagery:** {imagery}  
- **Gradient Effect:** {gradient_usage}  
- **Shadow and Depth:** {shadow_and_depth}  
- **Line Thickness:** {line_thickness}  
- **Corner Rounding:** {corner_rounding}  
- **Description:** {description}

### **User Input Types and Handling:**  
1. **Clear Specific Requests:** Update settings as specified by the user (e.g., "Make it rounded with softer colors").  
2. **Theme-Based Inputs:** For inputs like "banking" or "modern look," adjust the settings to align with the theme.  
    - Example: For "banking," use a corporate style, blue tones, and professional imagery like graphs or buildings.  
3. **Abstract or Descriptive Queries:** Interpret abstract inputs like "playful" or "techy" and adjust attributes accordingly.  
4. **Ambiguous or Invalid Queries:**  
    - Retain current settings without changes.  
    - Use the `general_response` to clarify what is missing or guide the user on refining their query (e.g., "Please specify what you'd like to update, such as color or style").  
5. **Combination Queries:** If inputs combine elements like "red corporate theme," prioritize updating the most relevant attributes for coherence.  
6. **No Clear Changes:** If the query is unrelated or lacks actionable details, keep all settings unchanged and offer friendly guidance.  
7. **If style is mentioned:** Update the style attribute with the mentioned style. Choices are: *outline, fill, lineal-color, hand-drawn.* only

### **Output Requirements:**  
For each query, return updated values for all attributes, or retain the existing ones if no change is needed. Always include a creative and user-friendly `general_response` to explain updates or offer guidance.  

### **Examples:**  
Case: When input contain theme
**Query:** "monkey icon"   or "monkey theme/style or anything related" in this case descriptio will be what in the imagery
**Output:**  
- Color Palette: Blue  
- Iconography: Minimalistic, Professional  
- Brand Style: Corporate  
- Imagery: Monkey, Trees  
- Gradient Usage: Subtle Gradient  
- Shadow and Depth: Medium Shadows  
- Line Thickness: Medium  
- Corner Rounding: Slightly Rounded  
- Description: Monkey
- General Response: Updated the design to align with the 'monkey' theme. Let me know if you'd like further adjustments.  

**Query:** "Change it!"  
**Output:**  
- (No changes to settings)  
- General Response: Please clarify what you’d like to change (e.g., colors, style, or theme). Let me know how I can assist you further!  

Case: When input contain object and color
**Query:** "white heart"
**Output:**
- Color Palette: White
- Iconography: Heart
- Brand Style: Corporate
- Imagery: Heart
- Gradient Usage: Subtle Gradient
- Shadow and Depth: Medium Shadows
- Line Thickness: Medium
- Corner Rounding: Slightly Rounded
- Description: Heart
- General Response: Updated the design to align with the 'white heart' theme. Let me know if you'd like further adjustments.

Case: When input contain both color and shape
**Query:** "Red Filled" 
**Output:**
- Color Palette: Red
- Iconography: Filled
- Brand Style: Corporate
- Imagery: Filled
- Gradient Usage: Subtle Gradient
- Shadow and Depth: Medium Shadows
- Line Thickness: Medium
- Corner Rounding: Slightly Rounded
- Description: {description} (unchaged)
- Style: fill
- General Response: Updated the design to align with the color 'red' and shape 'filled'.     Let me know if you'd like further adjustments.

Case: When input contain only general term
**Query:** "playful and vibrant"  
**Output:**  
- Color Palette: Gradient  
- Iconography: Rounded, Fun
- Brand Style: Playful, Modern  
- Imagery: Balloons, Stars  
- Gradient Usage: Vibrant Gradient
- Shadow and Depth: Soft Shadows
- Line Thickness: Medium  
- Corner Rounding: Fully Rounded
- Description: Playful, Vibrant, Fun, Modern
- General Response: Adjusted the design to a playful and vibrant style. Let me know if you'd like further tweaks!  

Case: When input contain only terms e.g "banana", "cat", etc
**Query:** "banana"  
**Output:**  
- Color Palette: yellow
- Iconography: Banana
- Brand Style: Corporate
- Imagery: Banana
- Gradient Usage: Subtle Gradient
- Shadow and Depth: Medium Shadows
- Line Thickness: Medium
- Corner Rounding: Slightly Rounded
- Description: Banana
- General Response: Updated the design to align with the 'banana' theme. Let me know if you'd like further adjustments.

Case: When input contain color and term e.g  "pink elephant", "red cow", etc
**Query:** "red cow"
**Output:**  
- Color Palette: Red
- Iconography: Minimalistic, Professional
- Brand Style: Corporate
- Imagery: Cow
- Gradient Usage: Subtle Gradient
- Shadow and Depth: Medium Shadows
- Line Thickness: Medium
- Corner Rounding: Slightly Rounded
- Description: Cow
- General Response: Updated the design to align with the 'red cow' and 'pink elephant' themes. Let me know if you'd like further adjustments.

Case: For any query use logicand creativity to update the design

### **Error-Proofing:**  
- Always ensure that shape-related updates use one of these: *outline, fill, lineal-color, hand-drawn.*  
- Retain settings and provide suggestions when inputs are invalid or unclear.  
- Keep the conversation user-friendly, precise, and creative.  
- You should never add shape/color in description field.

    """
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
                        description=icon_attributes.get("description", " "),
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
        You are an AI designed to classify queries into one of three categories: "color," "shape," or "general." Your task is to analyze the content of each query and determine its category based on the following rules:

        ### **Classification Rules:**  
        1. If the query mentions only a color, classify it as "color."  
        2. If the query mentions only a shape, classify it as "shape," ensuring the shape matches one of the following: *outline, fill, lineal-color, hand-drawn.*  
        3. If the query combines colors or shapes with general terms (e.g., "theme," "view," "style", "red cow", "outline, blue") or describes a combination of both, classify it as "general."  
        4. If the query contains descriptive terms without a clear color or shape, classify it as "general."  
        5. Always prioritize "general" if both a color and shape are mentioned.  

        **Output:**  
        Return the category as "color," "shape," or "general" based on the rules above. 
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
        Find closet or exact match of gradient, solid-black, multicolor, azure, black, blue, chartreuse,
         cyan, gray, green, orange, red, rose, spring-green, violet, white, yellow For example, if the input is "make the icon color pink or just pink," the output should be "rose." OR Golder if the input is "make the icon color gold or just gold," the output should be "yellow"(from the list). Dont return "None" always response the closest or exact match from list.
         some more examples:
            - "pink" -> "rose"
            - "gold" -> "yellow"
            - "purple" -> "violet"
            - "silver" -> "gray"
            - "sky blue" -> "azure"
            - "lime" -> "chartreuse"
            - and so on...

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