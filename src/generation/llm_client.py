import asyncio
from typing import List, Optional, Any
from openai import AsyncAzureOpenAI
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aiolimiter import AsyncLimiter
from src.settings import settings

class UnifiedAIClient:
    """
    A unified async client for Azure AI Foundry models with built-in rate-limiting and exponential backoff.
    Supports both Project Connection Strings (Foundry SDK) and Standard API Key configs.
    """
    
    def __init__(self):
        # Async Limiter to throttle bulk operations
        self.limiter = AsyncLimiter(settings.requests_per_minute, 60)
        
        self.project_client: Optional[AIProjectClient] = None
        self.inference_client: Optional[AsyncAzureOpenAI] = None

    async def initialize(self):
        """Asynchronously initialize the clients based on available configuration."""
        if self.inference_client is not None:
            return

        if settings.project_connection_string:
            credential = DefaultAzureCredential()
            self.project_client = AIProjectClient.from_connection_string(
                credential=credential,
                conn_str=settings.project_connection_string,
            )
            # Retrieve the AzureOpenAI async client from the unified Foundry Project Client
            self.inference_client = await self.project_client.inference.get_azure_openai_client(
                api_version=settings.api_version
            )
        else:
            # Fallback to standard AsyncAzureOpenAI if using standalone keys
            self.inference_client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=settings.api_version,
                azure_endpoint=settings.azure_openai_endpoint
            )

    async def close(self):
        """Cleanly close underlying HTTP clients."""
        if self.project_client:
            await self.project_client.close()
        elif self.inference_client:
            await self.inference_client.close()

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True
    )
    async def generate_lore(self, prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.7) -> str:
        """
        High-throughput text generation for bulk lore using the mini model series.
        Wrapped with rate-limiting and exponential backoff.
        """
        async with self.limiter:
            await self.initialize()
            response = await self.inference_client.chat.completions.create(
                model=settings.bulk_lore_deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True
    )
    async def synthesize_reasoning(self, prompt: str, system_prompt: str) -> str:
        """
        Strict constraint-following generation for Multi-hop Q&A and Graph validation.
        Uses the frontier reasoning deployment (e.g., gpt-4o).
        """
        async with self.limiter:
            await self.initialize()
            response = await self.inference_client.chat.completions.create(
                model=settings.reasoning_deployment_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1  # Low temperature for strict reasoning
            )
            return response.choices[0].message.content

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """Generates an embedding vector for Semantic Distractors."""
        async with self.limiter:
            await self.initialize()
            response = await self.inference_client.embeddings.create(
                model=settings.embedding_deployment_name,
                input=text
            )
            return response.data[0].embedding
