from typing import List,Literal,Dict,Any
from pydantic import BaseModel,Field

## Classification Output field
class Classification(BaseModel):
    quote: List[str] = Field(..., description="Claim or opinion text")
    order: List[int] = Field(..., description="Numerical order of the claim or opinion")
    type: List[str] = Field(..., description="Type: claim or opinion")
    claimType: List[str] = Field(..., description="Category: project, industry, or other")

    def to_json_structure(self) -> Dict[str, Any]:
        """Convert the classification output to the required JSON structure."""
        json_data = {"type": {"claim": [], "opinion": []}}

        for q, o, t, ct in zip(self.quote, self.order, self.type, self.claimType):
            if t.lower() == "claim":
                json_data["type"]["claim"].append({"claim-type": ct, "quote": q, "order": o})
            elif t.lower() == "opinion":
                json_data["type"]["opinion"].append({"quote": q, "order": o})

        return json_data
    
class FinalResponse(BaseModel):
    feedback: str = Field(description="Detailed feedback about the response")
    validity: Literal["valid", "Invalid"] = Field(description="Whether the quote is valid or invalid")
    response_strength: Literal["Strong", "Average", "Weak"] = Field(description="Assessment of the response strength")
    strength_explanation: str = Field(description="Brief explanation of the response strength rating")
    recommendations: List[str] = Field(description="List of recommendations to improve the response")
    chunks: List[Dict] = Field(description="Source chunks used for reference, including metadata")


class State(BaseModel):
    input_text: str
    classification_node:Any
    embedding_node: Any
    final_response: Any
    projectCollection_id: str
    industryCollection_id: str