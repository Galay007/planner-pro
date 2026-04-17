from pydantic import BaseModel

class EmitRequest(BaseModel):
    message: str
    event_type: str