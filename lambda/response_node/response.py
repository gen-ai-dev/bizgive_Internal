import json
from pydantic import BaseModel, Field
from typing import Dict, List
from langchain_openai import ChatOpenAI
import os
import sys
from utils.aws_utils import get_project_config

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.join(current_dir, '..')
sys.path.append(root_dir)

from database.data_retrieval import initialize_db_retriever

def load_system_prompt():
    file_path = os.path.join("updated_code", "lambda", "response_node", "prompt.txt")
    with open(file_path, "r") as file:
        return file.read()

def lambda_handler(event, context):
    structured_json = event.get("processed_text", {})

    system_prompt = load_system_prompt()

    


