import json
from pydantic import BaseModel, Field
from typing import Dict, List
from langchain_openai import ChatOpenAI
import os

model = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0)

def load_system_prompt():
    file_path = os.path.join("updated_code", "lambda", "classification_node", "prompt.txt")
    with open(file_path, "r") as file:
        return file.read()

def lambda_handler(event, context):
    input_text = event.get("input_text", "")

    system_prompt = load_system_prompt()

    final_prompt  = '''
                    [SYSTEM_PROMPT]
                    {system_prompt}
                    [USER_PROMPT]
                    {input_text}
                    '''

    processed_text = llm.invoke(final_prompt)

    return {"processed_text": processed_text}