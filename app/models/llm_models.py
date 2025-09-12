"""
LLM-related Pydantic models
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum


class MessageRole(str, Enum):
    """Message role enumeration"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """Message model"""
    role: MessageRole
    content: str


class LLMUsage(BaseModel):
    """LLM usage statistics model"""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMRequest(BaseModel):
    """LLM request model"""
    messages: List[Message]
    model: Optional[str] = None
    max_tokens: int = 300
    temperature: float = 0.1
    stream: bool = False


class LLMResponse(BaseModel):
    """LLM response model"""
    content: str
    usage: LLMUsage
    model_used: str
    finish_reason: Optional[str] = None
    error: Optional[str] = None
