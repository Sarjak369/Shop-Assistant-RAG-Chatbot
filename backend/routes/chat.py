from fastapi import APIRouter
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from backend.services.openai_chain import generate_response


router = APIRouter()

# Request format for /chat endpoint


class ChatRequest(BaseModel):
    query: str
    history: List[str] = []


@router.post("/chat")
def chat(request: ChatRequest):
    """
    API endpoint that:
    - Takes a query + history from the frontend (Postman, UI, etc.)
    - Calls generate_response() from openai_chain.py
    - Returns structured JSON with response + updated history
    """
    result = generate_response(request.query, request.history)
    return result
