from pydantic import BaseModel

class CodeReviewAction(BaseModel):
    review: str

class CodeReviewObservation(BaseModel):
    code_snippet: str
    feedback: str
    score: float
    reward: float = 0.0
    done: bool = False