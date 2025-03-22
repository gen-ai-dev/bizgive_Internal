import logging
import os
from fastapi import HTTPException, status
from langchain_openai import ChatOpenAI

# Configure logging
logger = logging.getLogger("Letter Response Node")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

def initialize_model():
    """
    Initialize and return the language model with error handling.
    
    Returns:
        The initialized language model
        
    Raises:
        HTTPException: If model initialization fails
    """
    try:
        model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)
        logger.info("Language model initialized successfully")
        return model
    except Exception as e:
        logger.error(f"Failed to initialize language model: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to initialize language model: {str(e)}"
        )

def load_system_prompt():
    """
    Load system prompt from file with error handling.
    
    Returns:
        str: The system prompt content
        
    Raises:
        HTTPException: If prompt file cannot be loaded
    """
    try:
        file_path = os.path.join("updated_code", "lambda", "classification_node", "prompt.txt")
        with open(file_path, "r") as file:
            prompt = file.read()
            logger.info(f"System prompt loaded from {file_path}")
            return prompt
    except FileNotFoundError:
        logger.error(f"System prompt file not found at {file_path}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System prompt file not found"
        )
    except Exception as e:
        logger.error(f"Error loading system prompt: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load system prompt: {str(e)}"
        )

def lambda_handler(event, context):
    """
    Main Lambda function handler with error handling.
    
    Args:
        event: Lambda event object containing input parameters
        context: Lambda context object
        
    Returns:
        Dict containing processed text
    """
    try:
        # Extract input text
        input_text = event.get("input_text", "")
        if not input_text:
            logger.warning("Empty input text received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Input text is required"
            )
            
        logger.info(f"Processing input text (length: {len(input_text)})")
        
        # Load system prompt
        system_prompt = load_system_prompt()
        
        # Initialize model
        model = initialize_model()
        
        # Prepare and format prompt
        final_prompt = f'''
                        [SYSTEM_PROMPT]
                        {system_prompt}
                        [USER_PROMPT]
                        {input_text}
                        '''
        
        # Invoke model
        try:
            logger.info("Invoking language model")
            processed_text = model.invoke(final_prompt)
            logger.info("Model response received successfully")
            
            # Return processed text
            return {"processed_text": processed_text}
            
        except Exception as e:
            logger.error(f"Error invoking language model: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing text: {str(e)}"
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.exception(f"Unexpected error in lambda_handler: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred: {str(e)}"
        )