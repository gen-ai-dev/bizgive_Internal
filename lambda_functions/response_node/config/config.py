import os
import logging
import boto3
from fastapi import HTTPException, status
from dotenv import load_dotenv
from langchain_aws.embeddings import BedrockEmbeddings
from langchain_aws import ChatBedrock

# Configure logging
logger = logging.getLogger("bedrock_service")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

##Load the environment variables
load_dotenv()

def get_bedrock_client() -> boto3.client:
    """
    Initialize and return the AWS Bedrock client with error handling.
    
    Returns:
        boto3.client: Configured Bedrock client
        
    Raises:
        HTTPException: If client initialization fails
    """
    try:
        region = os.getenv("AWS_DEFAULT_REGION")
        if not region:
            logger.error("AWS_DEFAULT_REGION environment variable not set")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="AWS region configuration missing"
            )
            
        bedrock_runtime = boto3.client(
            service_name="bedrock-runtime",
            region_name=region
        )
        logger.info(f"AWS Bedrock client initialized for region: {region}")
        return bedrock_runtime
        
    except boto3.exceptions.NoCredentialsError:
        logger.error("AWS credentials not found")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AWS authentication failed: credentials not found"
        )
    except boto3.exceptions.BotoCoreError as e:
        logger.error(f"AWS BotoCoreError: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AWS service error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error initializing Bedrock client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize AWS Bedrock client"
        )

def bedrock_embedding(model_id: str):
    """
    Initialize and return Bedrock embeddings with error handling.
    
    Args:
        model_id: The Bedrock model ID to use for embeddings
        
    Returns:
        BedrockEmbeddings: Configured embeddings client
        
    Raises:
        HTTPException: If embeddings initialization fails
    """
    try:
        if not model_id:
            logger.error("Model ID not provided for embeddings")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model ID is required for embeddings"
            )
            
        # Get the Bedrock client
        bedrock_runtime = get_bedrock_client()
        
        # Initialize Bedrock Embeddings
        embeddings = BedrockEmbeddings(
            model_id=model_id, 
            client=bedrock_runtime
        )
        
        logger.info(f"Bedrock embeddings initialized with model: {model_id}")
        return embeddings
        
    except ValueError as e:
        logger.error(f"Invalid value for embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid embeddings configuration: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock embeddings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing embeddings: {str(e)}"
        )

def initialize_llm(model_id: str, temperature: float):
    """
    Initialize and return the Bedrock LLM with error handling.
    
    Args:
        model_id: The Bedrock model ID to use
        temperature: Temperature setting for generation
        max_tokens: Maximum tokens for generation (default: 500)
        
    Returns:
        ChatBedrock: Configured LLM client
        
    Raises:
        HTTPException: If LLM initialization fails
    """
    try:
        # Validate inputs
        if not model_id:
            logger.error("Model ID not provided for LLM")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Model ID is required for LLM initialization"
            )
            
        if not 0 <= temperature <= 1:
            logger.warning(f"Temperature {temperature} out of recommended range (0-1)")
            
        # Initialize the LLM
        llm = ChatBedrock(
            model_id=model_id,
            model_kwargs=dict(temperature=temperature)
        )
        
        logger.info(f"Bedrock LLM initialized with model: {model_id}, temperature: {temperature}")
        return llm
        
    except ValueError as e:
        logger.error(f"Invalid value for LLM: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid LLM configuration: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock LLM: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing LLM: {str(e)}"
        )