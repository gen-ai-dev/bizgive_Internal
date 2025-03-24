import json
from pydantic import BaseModel, Field
from typing import Dict, List,Literal
import os
import sys
import logging
from fastapi import HTTPException, status
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from .config import initialize_llm

##setting up the logger
logger = logging.getLogger("classification_service")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)


class FinalResponse(BaseModel):
    feedback: str = Field(description="Detailed feedback about the response")
    validity: Literal["valid", "Invalid"] = Field(description="Whether the quote is valid or invalid")
    response_strength: Literal["Strong", "Average", "Weak"] = Field(description="Assessment of the response strength")
    strength_explanation: str = Field(description="Brief explanation of the response strength rating")
    recommendations: List[str] = Field(description="List of recommendations to improve the response")
    # chunks_list: List[Dict] = Field(description="Source chunks used for reference, including metadata")

def load_system_prompt() -> str:
    """Load system prompt from file with error handling."""
    try:
        file_path = r"lambda_functions\response_node\prompt.txt"
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

def initialize_model():
    """Initialize and return the language model with error handling."""
    try:
        # model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
        model = initialize_llm(model_id=os.getenv("LLM_MODEL"),temperature=0.0)
        # model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.1)
        return model
    except Exception as e:
        logger.error(f"Failed to initialize language model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to initialize language model"
        )

def lambda_handler(event, context):
    """
    Main Lambda function handler with comprehensive error handling.
    
    Args:
        event: Lambda event object containing input parameters
        context: Lambda context object
        
    Returns:
        Dict containing processed classification results
    """
    try:
        # Extract and validate input text
        input_text = event.get("input_text")
        if not input_text:
            logger.warning("Empty received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input is required but was empty"
            )
        
        logger.info(f"Processing Embeddings and Extractor Output)")
        
        # Load system prompt
        system_prompt = ""
        model = initialize_model()
        final_prompt = f'''
                        [SYSTEM_PROMPT]
                        {system_prompt}
                        [USER_PROMPT]
                        {input_text}
                        '''
        
        try:
            structured_llm = model.with_structured_output(FinalResponse)
            final_output = structured_llm.invoke(final_prompt)
            logger.info(f"Successfully the Extraction and Embeddings Outputs")
            return final_output
            
        except Exception as e:
            logger.error(f"Language model processing error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error during text processing: {str(e)}"
            )
            
    except HTTPException:
        raise
        
    except Exception as e:
        logger.exception(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during processing"
        )

    


