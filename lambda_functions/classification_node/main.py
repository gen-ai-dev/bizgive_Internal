import json
import logging
import boto3
import re
from pydantic import BaseModel, Field, validator
from langchain_community.chat_models import BedrockChat
from langchain_aws import ChatBedrock
from langchain_core.messages import AIMessage
from fastapi import HTTPException, status
from typing import Dict, List, Any, Optional

# Logger setup
logger = logging.getLogger("classification_service")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def load_system_prompt() -> str:
    """Load system prompt from file with error handling."""
    try:
        file_path = r"prompt.txt"
        with open(file_path, "rb") as file:
            return file.read()
    except FileNotFoundError:
        logger.error(f"System prompt file not found at {file_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System configuration error: prompt file not found"
        )
    except IOError as e:
        logger.error(f"Failed to read system prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System configuration error: failed to read prompt file"
        )



# Classification Model
class Classification(BaseModel):
    quote: List[str] = Field(..., description="Claim or opinion text")
    order: List[int] = Field(..., description="Numerical order of the claim or opinion")
    type: List[str] = Field(..., description="Type: claim or opinion")
    claimType: List[str] = Field(..., description="Category: project, industry, or other")

    def to_json_structure(self) -> Dict[str, Any]:
        """Convert the classification output to the required JSON structure."""
        json_data = {"type": {"claim": [], "opinion": []}}

        for q, o, t, ct in zip(self.quote, self.order, self.type, self.claimType):
            if t.lower() == "claim":
                json_data["type"]["claim"].append({"claim-type": ct, "quote": q, "order": o})
            elif t.lower() == "opinion":
                json_data["type"]["opinion"].append({"quote": q, "order": o})

        return json_data

# Initialize AWS Bedrock model
def initialize_model():
    """Initialize and return the Bedrock Claude model."""
    try:
        # Create client with explicit region
        bedrock_client = boto3.client("bedrock-runtime", region_name="eu-central-1")
        
        # Pass client to model but don't include region in model_kwargs
        model = ChatBedrock(
            client=bedrock_client,
            model_id="anthropic.claude-3-5-sonnet-20240620-v1:0",
            model_kwargs={} # Remove region from here
        )
        return model
    except Exception as e:
        # Log more specific AWS error details
        logger.error(f"Failed to initialize Claude model: {str(e)}", exc_info=True)
        if hasattr(e, "response"):
            logger.error(f"AWS Error Response: {e.response}")
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Claude model initialization failed")

# Function to clean and extract valid JSON
def extract_json(text):
    """Extracts a valid JSON string from Claude's response."""
    try:
        match = re.search(r"\{.*\}", text, re.DOTALL)  # Extract JSON-like text
        if match:
            json_str = match.group(0)
            return json.loads(json_str)  # Convert to JSON
        else:
            raise ValueError("No valid JSON found in response.")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON decoding failed: {str(e)}")


# Lambda Function Handler
def lambda_handler(event, context):
    """AWS Lambda handler for processing text classification."""
    try:
        input_text = event.get("input_text")
        if not input_text:
            logger.warning("Empty input text received")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Input text is required")

        logger.info(f"Processing input text: {input_text}")

        model = initialize_model()
        system_prompt = load_system_prompt()
        final_prompt = f'''
                        [SYSTEM_PROMPT]
                        {system_prompt}
                        [USER_PROMPT]
                        {input_text}
                        '''

        # Invoke Claude Model
        try:
            structured_llm = model.with_structured_output(Classification)
            processed_text = structured_llm.invoke(final_prompt)

            # Extract raw text from AIMessage
            if isinstance(processed_text, AIMessage):
                response_text = processed_text.content  # Extract AIMessage content
            else:
                response_text = str(processed_text)

            logger.info(f"Claude Response: {response_text}")

            # Attempt to parse JSON response
            try:
                #response_json = extract_json(response_text)
                #classification = Classification(**response_json)
                return processed_text.to_json_structure()
            except ValueError as e:
                logger.error(f"Failed to parse JSON: {str(e)}", exc_info=True)
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Claude response is not valid JSON")

        except Exception as e:
            logger.error(f"Error invoking Claude model: {str(e)}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error invoking Claude model")

    except HTTPException as http_error:
        raise http_error

    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")
