import os
import sys
import boto3

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
sys.path.append(root_dir)

import jwt
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from langchain_community.callbacks.manager import get_bedrock_anthropic_callback
from config.aws_config import initialize_llm
from langchain_chain_funs.db_retriever import initialize_db_retriever
from langchain_chain_funs.chains import create_rag_chain
from user_utils.user_utils import extract_json_fromtring,get_follow_up_counter
from langchain_chain_funs.query import ask_question_stream, unethical_stream
from utils.aws_utils import get_project_config
from user_utils.pii_remover import detect_and_mask_pii
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

lambda_client = boto3.client('lambda', region_name=AWS_REGION)
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")  # Change to your region
ORCHESTRATOR_LAMBDA_FUNCTION_NAME = os.getenv("ORCHESTRATOR_LAMBDA_FUNCTION_NAME", "your-lambda-function-name")
LETTER_RES_LAMBDA_FUNCTION_NAME = os.getenv("LETTER_RES_LAMBDA_FUNCTION_NAME", "your-lambda-function-name")

def invoke_lambda(function_name, payload):
    """Invoke an AWS Lambda function and return the response."""
    try:
        response = lambda_client.invoke(
            FunctionName=function_name,
            InvocationType="RequestResponse",
            Payload=json.dumps(payload)
        )
        # Read and decode the response payload
        result = json.loads(response["Payload"].read().decode())
        return result
    except Exception as e:
        raise Exception(f"Lambda invocation error: {str(e)}")


# FastAPI route to handle POST request
@router.post('/api/bgai/responseflow')
async def responseflow(request: Request, token: str = Depends(oauth2_scheme)):
    # Decode the JWT token
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        custom_entity = payload.get('custom:entity') 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Check for the allowed custom entity
    if custom_entity != "cePublic":
        raise HTTPException(status_code=403, detail="You are not allowed to perform this operation")

    data = await request.json()
    question_time = datetime.now().strftime("%Y%m%d %H:%M:%S")

    # Extract parameters from request body
    visitor_id = data.get('visitorID')
    asset_id = data.get('assetID')
    projectCollection_id = data.get('projectCollection')
    industryCollection_id = data.get('industryCollection')
    question = data.get('text')
    flow = data.get('flow')

    # Check for missing parameters
    if not visitor_id or not asset_id or not project_id or not question:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    try:
        event = {"input_text": question}
        lambda_response = invoke_lambda(LAMBDA_FUNCTION_NAME, event)
        final_output = lambda_response.get("final_output", "No response generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"response": final_output, "timestamp": question_time}

@router.post('/api/bgai/letterresflow')
async def responseflow(request: Request, token: str = Depends(oauth2_scheme)):
    # Decode the JWT token
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        custom_entity = payload.get('custom:entity') 
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.PyJWTError:
        raise HTTPException(status_code=403, detail="Invalid token")

    # Check for the allowed custom entity
    if custom_entity != "cePublic":
        raise HTTPException(status_code=403, detail="You are not allowed to perform this operation")

    data = await request.json()
    question_time = datetime.now().strftime("%Y%m%d %H:%M:%S")

    # Extract parameters from request body
    visitor_id = data.get('visitorID')
    question = data.get('text')

    # Check for missing parameters
    if not visitor_id or not asset_id or not project_id or not question:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    try:
        event = {"input_text": question}
        lambda_response = invoke_lambda(LETTER_RES_LAMBDA_FUNCTION_NAME, event)
        final_output = lambda_response.get("final_output", "No response generated")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"response": final_output, "timestamp": question_time}    