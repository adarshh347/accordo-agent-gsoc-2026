"""
LLM client wrapper for Groq API.

Provides a simple interface for calling the Groq LLM with
configurable models and error handling.
"""

import json
import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class LLMResponse:
    """Response from the LLM."""
    content: str
    model: str
    usage: dict
    success: bool
    error: Optional[str] = None


class GroqClient:
    """
    Client for interacting with Groq's LLM API.
    
    Uses langchain-groq for integration with CrewAI.
    """
    
    DEFAULT_MODEL = "llama-3.3-70b-versatile"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ):
        """
        Initialize the Groq client.
        
        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
            model: Model to use. Defaults to llama-3.3-70b-versatile.
            temperature: Temperature for generation (0.0 to 1.0).
            max_tokens: Maximum tokens to generate.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Groq API key not provided. Set GROQ_API_KEY environment variable "
                "or pass api_key to constructor. Get a free key at https://console.groq.com/keys"
            )
        
        self.model = model or os.getenv("GROQ_MODEL", self.DEFAULT_MODEL)
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize the Groq client
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize the underlying Groq client."""
        try:
            from groq import Groq
            self._client = Groq(api_key=self.api_key)
        except ImportError:
            # Fallback to langchain-groq if groq package not available
            try:
                from langchain_groq import ChatGroq
                self._langchain_client = ChatGroq(
                    api_key=self.api_key,
                    model=self.model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                self._client = None  # Use langchain mode
            except ImportError:
                raise ImportError(
                    "Neither 'groq' nor 'langchain-groq' package is installed. "
                    "Install with: pip install groq or pip install langchain-groq"
                )
    
    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> LLMResponse:
        """
        Send a chat request to the LLM.
        
        Args:
            system_prompt: System message defining the assistant's role.
            user_prompt: User message with the actual request.
            temperature: Override temperature for this request.
            
        Returns:
            LLMResponse with the generated content.
        """
        temp = temperature if temperature is not None else self.temperature
        
        try:
            if self._client is not None:
                # Use native Groq client
                response = self._client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temp,
                    max_tokens=self.max_tokens
                )
                
                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                        "total_tokens": response.usage.total_tokens
                    },
                    success=True
                )
            else:
                # Use langchain client
                from langchain_core.messages import HumanMessage, SystemMessage
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                response = self._langchain_client.invoke(messages)
                
                return LLMResponse(
                    content=response.content,
                    model=self.model,
                    usage=response.response_metadata.get("usage", {}),
                    success=True
                )
                
        except Exception as e:
            return LLMResponse(
                content="",
                model=self.model,
                usage={},
                success=False,
                error=str(e)
            )
    
    def chat_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None
    ) -> tuple[Optional[dict], Optional[str]]:
        """
        Send a chat request expecting JSON response.
        
        Args:
            system_prompt: System message.
            user_prompt: User message.
            temperature: Override temperature.
            
        Returns:
            Tuple of (parsed_json, error_message).
            If successful, error_message is None.
            If failed, parsed_json is None.
        """
        response = self.chat(system_prompt, user_prompt, temperature)
        
        if not response.success:
            return None, response.error
        
        content = response.content.strip()
        
        # Try to extract JSON from the response
        # Handle case where LLM wraps in markdown code blocks
        if content.startswith("```"):
            # Extract content between code blocks
            lines = content.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            content = "\n".join(json_lines)
        
        try:
            parsed = json.loads(content)
            return parsed, None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON response: {e}\nContent: {content[:500]}"


# Global client instance (lazy initialization)
_client: Optional[GroqClient] = None


def get_llm_client() -> GroqClient:
    """Get or create the global LLM client."""
    global _client
    if _client is None:
        _client = GroqClient()
    return _client


def chat(system_prompt: str, user_prompt: str) -> LLMResponse:
    """Convenience function for quick chat calls."""
    return get_llm_client().chat(system_prompt, user_prompt)


def chat_json(system_prompt: str, user_prompt: str) -> tuple[Optional[dict], Optional[str]]:
    """Convenience function for quick JSON chat calls."""
    return get_llm_client().chat_json(system_prompt, user_prompt)
