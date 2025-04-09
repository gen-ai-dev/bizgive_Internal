import  os
import sys

## Settings to allow imports from another folder or packages
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
sys.path.append(root_dir)

import json
import boto3
from langgraph.graph import StateGraph, START, END
import os
import logging
from state import State
import traceback
from botocore.exceptions import ClientError
#from classification_node import lambda_handler as classification_lambda
#from embedding_tool import lambda_handler as embedding_lambda
#from response_node import lambda_handler as response_lambda

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Constants for error messages
ERR_LAMBDA_INVOCATION = "Error invoking Lambda function {}: {}"
ERR_MISSING_ENV_VAR = "Missing required environment variable: {}"
ERR_WORKFLOW_EXECUTION = "Error during workflow execution: {}"

# Initialize AWS clients with error handling
try:
    lambda_client = boto3.client("lambda")
    logger.info("Successfully initialized AWS Lambda client")
except Exception as e:
    logger.critical(f"Failed to initialize AWS Lambda client: {str(e)}")
    raise

# Validate environment variables
required_env_vars = ['EXTRACTION_LAMBDA', 'EMBEDDINGS_LAMBDA', 'RESPONSE_LAMBDA']
missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
if missing_vars:
    for var in missing_vars:
        logger.critical(ERR_MISSING_ENV_VAR.format(var))
    raise ValueError(f"Missing environment variables: {', '.join(missing_vars)}")

FLOW_CONFIGS = {
    "respond": {
        "lambdas": {
            "extraction": os.environ['EXTRACTION_LAMBDA'],
            "embeddings": os.environ['EMBEDDINGS_LAMBDA'],
            "response": os.environ['RESPONSE_LAMBDA']
        }
    },
}

def invoke_lambda(function_name, payload):
    """
    Invoke an AWS Lambda function with error handling and logging.
    
    Args:
        function_name (str): The name of the Lambda function to invoke
        payload (dict): The payload to send to the Lambda function
        
    Returns:
        dict: The response from the Lambda function
        
    Raises:
        Exception: If there is an error invoking the Lambda function
    """
    try:
        logger.info(f"Invoking Lambda function: {function_name}")
        response = lambda_client.invoke(
            FunctionName=function_name,
            Payload=json.dumps(payload)
        )
        
        # Check for Lambda execution errors
        status_code = response.get("StatusCode", 500)
        if status_code != 200:
            logger.error(f"Lambda returned non-200 status: {status_code}")
            raise Exception(f"Lambda execution failed with status: {status_code}")
        
        # Check for function errors
        function_error = response.get("FunctionError")
        if function_error:
            error_payload = json.loads(response["Payload"].read().decode())
            error_message = error_payload.get("errorMessage", "Unknown error")
            logger.error(f"Lambda function error: {function_error} - {error_message}")
            raise Exception(f"Lambda function error: {error_message}")
        
        # Read and decode the response payload
        result = json.loads(response["Payload"].read().decode())
        
        # Validate response structure
        if not isinstance(result, dict):
            logger.warning(f"Unexpected response format from {function_name}: {type(result)}")
            raise ValueError(f"Lambda {function_name} returned invalid response format")
        
        logger.info(f"Successfully invoked Lambda: {function_name}")
        return result
        
    except ClientError as e:
        logger.error(ERR_LAMBDA_INVOCATION.format(function_name, str(e)))
        raise Exception(f"AWS Lambda service error: {str(e)}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from {function_name}: {str(e)}")
        raise Exception(f"Invalid JSON response from Lambda {function_name}")
    except Exception as e:
        logger.error(ERR_LAMBDA_INVOCATION.format(function_name, str(e)))
        raise

def classification_node(state: State) -> State:
    print(state.input_text)
    """Process the input text through the classification Lambda function."""
    try:
        logger.info("Starting classification node processing")
        if not state.input_text:
            logger.warning("No input text provided for classification")
            state["classification_node"] = ""
            return state
            
        response = invoke_lambda(FLOW_CONFIGS["respond"]["lambdas"]["extraction"], {"input_text": state.input_text})
        # response = classification_lambda({"input_text":state.input_text},None)
        logger.info("Classification node processing completed")
        
        return {"classification_node":response}
    except Exception as e:
        logger.error(f"Error in classification node: {str(e)}")
        raise e

def embedding_node(state: State) -> State:
    """Process the classified text through the embedding Lambda function."""
    try:
        logger.info("Starting embedding node processing")
        if not state.classification_node:
            logger.warning("No classified text provided for embedding")
            return state
            
        response = invoke_lambda(FLOW_CONFIGS["respond"]["lambdas"]["embeddings"], {"input_text": state.classification_node,"collection_id":state.projectCollection_id,"projectCollection":state.projectCollection_id,"industryCollection":state.industryCollection_id})
        # response = embedding_lambda({"input_text": state.classification_node,"collection_id":state.projectCollection_id,"projectCollection":state.projectCollection_id,"industryCollection":state.industryCollection_id},None)
            
        logger.info("Embedding node processing completed")
        return {"embedding_node":response}
    except Exception as e:
        logger.error(f"Error in embedding node: {str(e)}")
        raise e

def response_node(state: State) -> State:
    """Generate a response based on the embedded text."""
    try:
        logger.info("Starting response node processing")
        if not state.embedding_node:
            logger.warning("No embedded text provided for response generation")
            return state
            
        response = invoke_lambda(FLOW_CONFIGS["respond"]["lambdas"]["response"], {"input_text": state.embedding_node})
        # response = response_lambda({"input_text":state.embedding_node},None)
        logger.info("Response node processing completed")
        return {"final_response":response}
    except Exception as e:
        logger.error(f"Error in response node: {str(e)}")
        raise e

# def letter_res_node(state: State) -> State:
#     """Process the input text to generate a letter response."""
#     try:
#         logger.info("Starting letter response node processing")
#         if not state.get("input_text"):
#             logger.warning("No input text provided for letter response")
#             state["letter_response"] = "I'm sorry, I couldn't process your letter request."
#             return state
            
#         response = invoke_lambda("LambdaLetterRes", {"input_text": state["input_text"]})
        
#         if "processed_text" not in response:
#             logger.warning("Letter Response Lambda did not return 'processed_text'")
#             state["letter_response"] = "I'm sorry, I couldn't generate a proper letter response."
#         else:
#             state["letter_response"] = response["processed_text"]
            
#         logger.info("Letter response node processing completed")
#         return state
#     except Exception as e:
#         logger.error(f"Error in letter response node: {str(e)}")
#         # Provide graceful fallback
#         state["letter_response"] = "I apologize, but I encountered an error while generating a letter response."
#         state["letter_response_error"] = str(e)
#         return state

# Initialize the workflow graph
try:
    logger.info("Initializing workflow graph")
    workflow = StateGraph(State)
    
    # Add nodes
    workflow.add_node("classification", classification_node)
    workflow.add_node("embedding", embedding_node)
    workflow.add_node("response", response_node)
    # Uncomment to add letter response node
    # workflow.add_node("letter_response", letter_res_node)
    
    # Add edges
    workflow.add_edge(START, "classification")
    workflow.add_edge("classification", "embedding")
    workflow.add_edge("embedding", "response")
    workflow.add_edge("response", END)
    
    # Compile the graph
    graph = workflow.compile()
    logger.info("Workflow graph initialized and compiled successfully")
except Exception as e:
    logger.critical(f"Failed to initialize workflow graph: {str(e)}")
    raise

def lambda_handler(event, context):
    """
    AWS Lambda handler function to process input text through the workflow.
    
    Args:
        event (dict): The event data from the Lambda invocation
        context (LambdaContext): The context object provided by AWS Lambda
        
    Returns:
        dict: The final output from the workflow
    """
    try:
        '''logger.info("Orchastrator started")
        query_id = event.get('query_id', '')      
        question = event.get('text', '')        
        project_collection = event.get('projectCollection', '')        
        industry_collection = event.get('industryCollection', '')        
        visitor_id = event.get('visitorID', '')        
        asset_id = event.get('assetID', '')        
        # Create a new dictionary with the same structure        
        event_dict = {            
                        "input_text": question,            
                        "classification_node": None,            
                        "embedding_node": None,            
                        "final_response": None,            
                        "projectCollection_id": "project_collection_id",            
                        "industryCollection_id": "industry_collection_id"     
                    }'''
        input_text = event["input_text"]
        # logger.info(f"Processing input: {input_text[:50]}{'...' if len(input_text) > 50 else ''}")
        config = {"configurable": {"thread_id": event["query_id"]}}
        result_state = graph.invoke(input_text,config=config)
        print(result_state)
        response_text = result_state["final_response"]
        
        logger.info("Lambda handler completed successfully")
        return {"final_output": response_text}
        
    except Exception as e:
        error_details = traceback.format_exc()
        logger.error(f"{ERR_WORKFLOW_EXECUTION.format(str(e))}\n{error_details}")
        raise e
    


# complaint_letter = """
# [Your Name]
# [Your Address]
# [Your Contact Information]
# [Date]

# [Recipient Name/Title]
# [Recipient Address]

# **Subject: Objection to the Proposed M74 Renewable Energy Park**

# Dear [Recipient Name/Title],

# I am writing to formally lodge my complaint regarding the plans for the proposed M74 Renewable Energy Park. As a local resident of the Crawfordjohn area, I feel compelled to express my deep concerns about the project's potential impact on our community and environment.

# Specifically, I believe that the Crawfordjohn area is already significantly saturated with wind turbines. The proliferation of these turbines has severely degraded the previously scenic outlook from our village, transforming our once picturesque landscape.

# While I am an enthusiastic supporter of renewable energy initiatives, I believe there is a point at which the transformation of an attractive and peaceful rural environment into a virtual industrialized wasteland becomes unacceptable. The cumulative impact of these developments is detrimental to the quality of life and the aesthetic value of our region.

# Furthermore, I am particularly concerned about the proposed solar farm on part of Black Hill. I live in the shadow of Black Hill, which, as you know, hosts significant prehistoric artifacts. I understood that this historical significance offered the hill some protection against further wind turbine installations, and this understanding appears to have been accurate. However, the inclusion of a solar farm in this latest proposal feels like an act of vandalism against a valuable historical asset.

# Therefore, I would like to formally record my objection to these proposals in their current form. I urge you to reconsider the scale and location of this project, taking into account the existing saturation of renewable energy infrastructure in our area and the preservation of our historically significant landscapes.

# Thank you for your attention to this important matter.

# Sincerely,

# [Your Signature]
# [Your Typed Name]
# """
# event = {"input_text": complaint_letter,
#                  "classification_node":None,
#                  "embedding_node":None,
#                  "final_response":None,
#                  "projectCollection_id":"test_2",
#                  "industryCollection_id":"test_2"
#         }

# print(lambda_handler(event,None))
