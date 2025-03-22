import json
import boto3
from langgraph.graph import StateGraph
from langgraph.pregel import stateful
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client("lambda")

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
    response = lambda_client.invoke(
        FunctionName=function_name,
        Payload=json.dumps(payload)
    )
    # Read and decode the response payload
    result = json.loads(response["Payload"].read().decode())
    return result

class State(dict):
    def __init__(self, input_text):
        super().__init__()
        self["input_text"] = input_text
        self["classification_node"] = None
        self["embedding_node"] = None
        self["response"] = None
        self["letter_response"] = None

@stateful
def classification_node(state: State) -> State:
    response = invoke_lambda("LambdaClassification", {"input_text": state["input_text"]})
    state["classification_node"] = response["processed_text"]
    return state

@stateful
def embedding_node(state: State) -> State:
    response = invoke_lambda("LambdaClassification", {"input_text": state["classification_node"]})
    state["embedding_node"] = response["processed_text"]
    return state

@stateful
def response_node(state: State) -> State:
    response = invoke_lambda("LambdaResponse", {"input_text": state["embedding_node"]})
    state["response"] = response["processed_text"]
    return state

@stateful
def letter_res_node(state: State) -> State:
    response = invoke_lambda("LambdaLetterRes", {"input_text": state["input_text"]})
    state["letter_response"] = response["processed_text"]
    return state


workflow = StateGraph(State)
workflow.add_node("classification", classification_node)
#workflow.add_node("embedding", embedding_node)
workflow.add_node("response", response_node)
#workflow.add_node("letter_responsse", letter_res_node)

graph = workflow.compile()

def lambda_handler(event, context):
    # Create state using the input text from the event
    state = State(input_text=event.get("input_text", ""))
    # Invoke the workflow, which updates the state dictionary through its nodes
    result_state = graph.invoke(state)
    # Return the final output from the 'letter_response' key
    return {"final_output": result_state["letter_response"]}

