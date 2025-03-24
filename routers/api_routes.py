import os
import json
import boto3
import jwt
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from dotenv import load_dotenv
from datetime import datetime
from lambda_functions import orchestrator_lambda

load_dotenv()

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
AWS_DEFAULT_REGION = os.getenv("AWS_REGION", "eu-west-2")
lambda_client = boto3.client('lambda', region_name=AWS_DEFAULT_REGION)
ORCHESTRATOR_LAMBDA_FUNCTION_NAME = os.getenv("ORCHESTRATOR_LAMBDA_FUNCTION_NAME")

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
async def responseflow(request: Request):
    # # Decode the JWT token
    # try:
    #     payload = jwt.decode(token, options={"verify_signature": False})
    #     custom_entity = payload.get('custom:entity') 
    # except jwt.ExpiredSignatureError:
    #     raise HTTPException(status_code=401, detail="Token has expired")
    # except jwt.PyJWTError:
    #     raise HTTPException(status_code=403, detail="Invalid token")

    # # Check for the allowed custom entity
    # if custom_entity != "cePublic":
    #     raise HTTPException(status_code=403, detail="You are not allowed to perform this operation")

    data = await request.json()
    question_time = datetime.now().strftime("%Y%m%d %H:%M:%S")

    # Extract parameters from request body
    query_id = data.get('query_id')
    visitor_id = data.get('visitorID')
    asset_id = data.get('assetID')
    projectCollection_id = data.get('projectCollection')
    industryCollection_id = data.get('industryCollection')
    question = data.get('text')
    flow = data.get('flow')

    # Check for missing parameters
    if not visitor_id or not asset_id or not projectCollection_id or not question:
        raise HTTPException(status_code=400, detail="Missing required parameters")

    try:
        event = {"input_text": question,
                 "classification_node":None,
                 "embedding_node":None,
                 "final_response":None,
                 "projectCollection_id":projectCollection_id,
                 "industryCollection_id":industryCollection_id,
                }
        lambda_response = invoke_lambda(ORCHESTRATOR_LAMBDA_FUNCTION_NAME, {"input_text":event,"query_id":query_id})
        # lambda_response = orchestrator_lambda({"input_text":event,"query_id":query_id},None)
        final_output = lambda_response.get("final_output")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"response": final_output}

# @router.post('/api/bgai/letterresflow')
# async def responseflow(request: Request, token: str = Depends(oauth2_scheme)):
#     # Decode the JWT token
#     try:
#         payload = jwt.decode(token, options={"verify_signature": False})
#         custom_entity = payload.get('custom:entity') 
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token has expired")
#     except jwt.PyJWTError:
#         raise HTTPException(status_code=403, detail="Invalid token")

#     # Check for the allowed custom entity
#     if custom_entity != "cePublic":
#         raise HTTPException(status_code=403, detail="You are not allowed to perform this operation")

#     data = await request.json()
#     question_time = datetime.now().strftime("%Y%m%d %H:%M:%S")

#     # Extract parameters from request body
#     visitor_id = data.get('visitorID')
#     question = data.get('text')

#     # Check for missing parameters
#     # if not visitor_id or not asset_id or not project_id or not question:
#     #     raise HTTPException(status_code=400, detail="Missing required parameters")

#     try:
#         event = {"input_text": question}
#         lambda_response = invoke_lambda(LETTER_RES_LAMBDA_FUNCTION_NAME, event)
#         final_output = lambda_response.get("final_output", "No response generated")
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))

#     return {"response": final_output, "timestamp": question_time}    