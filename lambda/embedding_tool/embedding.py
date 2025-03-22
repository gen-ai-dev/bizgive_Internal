import boto3
import logging
from typing import Dict, List, Any, Optional
import json
from fastapi import HTTPException, status
from database.data_retrieval import initialize_db_retriever

# Configure logging
logger = logging.getLogger("reference_service")
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)

## Sample this will come from the payload
collection_id = None  
projectCollection = None  
industryCollection = None  
config_data = {}  

def get_reference(query: str, type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve reference context based on the query and type.
    
    Args:
        query: The search query text
        type: The type of reference to retrieve (None, "project", or "industry")
        
    Returns:
        List of context documents matching the query
        
    Raises:
        HTTPException: If reference retrieval fails
    """
    try:
        if not query:
            logger.warning("Empty query provided to get_reference")
            return []
        
        logger.info(f"Getting references for query (length: {len(query)}) with type: {type}")
        
        # Validate configuration
        if 'top_k' not in config_data or 'embeddings_model' not in config_data:
            logger.error("Missing required configuration for retriever")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Reference retrieval configuration is incomplete"
            )
        
        # Initialize the appropriate retriever based on type
        retriever = None
        if type is None:
            # Check if collection_id is defined
            if not collection_id:
                logger.error("Default collection ID is not defined")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Reference collection not configured"
                )
                
            logger.debug(f"Initializing default retriever with collection: {collection_id}")
            retriever = initialize_db_retriever(
                collectionID=collection_id, 
                top_k=config_data['top_k'], 
                embeddings_model=config_data['embeddings_model'], 
                # industry_collectionID=None
            )
            
        elif type == "project":
            # Check if projectCollection is defined
            if not projectCollection:
                logger.error("Project collection ID is not defined")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Project reference collection not configured"
                )
                
            logger.debug(f"Initializing project retriever with collection: {projectCollection}")
            retriever = initialize_db_retriever(
                collectionID=projectCollection, 
                top_k=config_data['top_k'], 
                embeddings_model=config_data['embeddings_model'], 
                # industry_collectionID=None
            )
            
        elif type == "industry":
            # Check if both collections are defined
            if not projectCollection or not industryCollection:
                logger.error("Project or industry collection ID is not defined")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Industry reference collections not configured"
                )
                
            logger.debug(f"Initializing industry retriever with collections: {projectCollection}, {industryCollection}")
            retriever = initialize_db_retriever(
                collectionID=projectCollection, 
                # industry_collectionID=industryCollection, 
                top_k=config_data['top_k'], 
                embeddings_model=config_data['embeddings_model']
            )
            
        else:
            logger.warning(f"Unknown reference type: {type}, using default retriever")
            if not collection_id:
                logger.error("Default collection ID is not defined")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Reference collection not configured"
                )
                
            retriever = initialize_db_retriever(
                collectionID=collection_id, 
                top_k=config_data['top_k'], 
                embeddings_model=config_data['embeddings_model'], 
                # industry_collectionID=None
            )
        
        # Execute the query
        context = retriever.invoke(query)
        logger.info(f"Retrieved {len(context) if context else 0} reference documents")
        return context
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.error(f"Error retrieving references: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve references: {str(e)}"
        )

def lambda_handler(event, context):
    """
    Main Lambda function handler for enriching structured claims and opinions with references.
    
    Args:
        event: Lambda event object containing input parameters
        context: Lambda context object
        
    Returns:
        Dict containing the enriched data structure
    """
    try:
        # Extract and validate the processed text from event
        structured_json = event.get("input_text", {})
        
        # Extract claims and opinions
        claims = structured_json["type"].get("claim", [])
        opinions = structured_json["type"].get("opinion", [])
        
        logger.info(f"Processing {len(claims)} claims and {len(opinions)} opinions")

        # Process claims
        if claims:
            for i, claim in enumerate(claims):
                try:
                    # Validate claim structure
                    if "quote" not in claim or "claim-type" not in claim:
                        logger.warning(f"Claim {i} is missing required fields")
                        claim["context"] = []
                        continue
                        
                    logger.debug(f"Getting references for claim {i}: {claim['quote'][:50]}...")
                    claim["context"] = get_reference(claim["quote"], claim["claim-type"])
                    
                except Exception as e:
                    logger.error(f"Error processing claim {i}: {str(e)}")
                    claim["context"] = []
        
        # Process opinions
        if opinions:
            for i, opinion in enumerate(opinions):
                try:
                    # Validate opinion structure
                    if "quote" not in opinion:
                        logger.warning(f"Opinion {i} is missing required fields")
                        opinion["context"] = []
                        continue
                        
                    logger.debug(f"Getting references for opinion {i}: {opinion['quote'][:50]}...")
                    opinion["context"] = get_reference(opinion["quote"], None)
                    
                except Exception as e:
                    logger.error(f"Error processing opinion {i}: {str(e)}")
                    opinion["context"] = []
        
        logger.info("Successfully processed all claims and opinions")
        return {"claims":claims,"opinions":opinions}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
        
    except Exception as e:
        logger.exception(f"Unexpected error in lambda_handler: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reference enrichment failed: {str(e)}"
        )