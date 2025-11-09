"""Agent configuration schema using Pydantic"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Tool configuration schema"""
    name: str
    description: str
    handler: str  # Path to handler function
    parameters: Dict[str, Any]


class MemoryConfig(BaseModel):
    """Memory configuration schema"""
    enabled: bool = False
    type: str = "non_parametric"  # non_parametric or parametric
    top_k: int = 4
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    storage_type: str = "jsonl"  # database or jsonl
    storage_path: str = "memory/cases.jsonl"  # Path to JSONL file
    device: str = "auto"  # auto, cpu, cuda
    filter_negative: bool = True  # Filter out negative cases (reward=0) when retrieving
    include_negative_examples: bool = False  # Include negative examples in prompt (if not filtered)
    max_negative_examples: int = 2  # Max negative examples to show


class ModelConfig(BaseModel):
    """Model configuration schema"""
    provider: str = "openai"  # openai, gemini, anthropic
    model_name: str = "gpt-4o-mini"  # gpt-4.1-mini or gpt-4o-mini
    temperature: float = 0.7
    max_tokens: Optional[int] = 2000


class ConversationConfig(BaseModel):
    """Conversation configuration schema"""
    max_steps: int = 4
    enable_memory_injection: bool = True


class AgentConfig(BaseModel):
    """Main agent configuration schema"""
    agent: Dict[str, str] = Field(..., description="Agent metadata")
    tools: List[ToolConfig] = Field(default_factory=list)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)

    class Config:
        extra = "allow"  # Allow extra fields for flexibility

