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

class Classification(BaseModel):
    quote: List[str] = Field(..., description="Claim or opinion text")
    order: List[int] = Field(..., description="Numerical order of the claim or opinion")
    type: List[str] = Field(..., description="Type: claim or opinion")
    claimType: List[str] = Field(..., description="Category: project, industry, or other")

    def to_json_structure(self) -> Dict[str, Any]:
        """Convert the classification output to the required JSON structure."""
        json_data = {"type": {"claim": [], "opinion": []}}

        for q, o, t, ct in zip(self.quote, self.order, self.type, self.claimType):
            if t == "claim":
                json_data["type"]["claim"].append({"claim-type": ct, "quote": q, "order": o})
            elif t == "opinion":
                json_data["type"]["opinion"].append({"quote": q, "order": o})

        return json_data

def lambda_handler(event, context):
    # Extract input text and perform basic preprocessing (e.g., trimming and lowercasing)
    input_text = event.get("input_text", "")

    system_prompt = load_system_prompt()

    final_prompt  = '''
                    [SYSTEM_PROMPT]
                    {system_prompt}
                    [USER_PROMPT]
                    {input_text}
                    '''
    structured_llm = model.with_structured_output(Classification)
    processed_text = structured_llm.invoke(final_prompt)
    return {"processed_text": processed_text}

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