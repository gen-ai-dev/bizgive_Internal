import json
import logging
from typing import Dict, List, Any, Optional
import os
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from langchain_google_genai.chat_models import ChatGoogleGenerativeAI
from dotenv import load_dotenv
from .config import initialize_llm

##setting up the logger
logger = logging.getLogger("classification_service")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

# Load environment variables
load_dotenv()

##Structure to perform the classification
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

def load_system_prompt() -> str:
    """Load system prompt from file with error handling."""
    try:
        file_path = r"lambda_functions\classification_node\prompt.txt"
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
        # model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.1)
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
            logger.warning("Empty input text received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input text is required but was empty"
            )
        
        logger.info(f"Processing input text (length: {len(input_text)})")
        
        # Load system prompt
        # system_prompt = load_system_prompt()
        system_prompt = "Analyse the following:"
        model = initialize_model()
        # model = ChatGoogleGenerativeAI(model='gemini-2.0-flash',temperature=0.7)
        final_prompt = f'''
                        [SYSTEM_PROMPT]
                        {system_prompt}
                        [USER_PROMPT]
                        {input_text}
                        '''
        
        try:
            structured_llm = model.with_structured_output(Classification)
            processed_text = structured_llm.invoke(final_prompt)
            logger.info(f"Successfully processed text. Found {len(processed_text.quote)} classifications.")
            return processed_text.to_json_structure()
            
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

'''
{
 "type": {"claim":	[
	   		{"claim-type": "project"/"industry"/"other",
	    		"quote": "exact quote",
	    		"order": "Numerical position in the original text"},

	   		{"claim-type": "project"/"industry"/"other",
	    		"quote": "exact quote",
	    		"order": "Numerical position in the original text"}
	  		],

 	   "opinion":	[
             		{"quote": "exact quote",
	      		"order": "Numerical position in the original text"},
	     
             		{"quote": "exact quote",
	      		"order": "Numerical position in the original text"}
	    		]
	}
}
'''