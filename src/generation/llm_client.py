import asyncio
import httpx
from typing import List, Optional, Any, Dict
from openai import AsyncAzureOpenAI, AsyncOpenAI
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from aiolimiter import AsyncLimiter
from src.settings import settings

class UnifiedAIClient:
    """
    A unified async client for Azure AI Foundry models with built-in rate-limiting and exponential backoff.
    Manages distinct clients for Chat, Embeddings, Images, and Reranking (MaaS).
    """
    
    def __init__(self):
        self.limiter = AsyncLimiter(settings.requests_per_minute, 60)
        
        self.project_client: Optional[AIProjectClient] = None
        self.chat_client: Optional[Any] = None
        self.embedding_client: Optional[Any] = None
        self.image_client: Optional[Any] = None

    def _create_openai_client(self, endpoint: Optional[str], api_key: Optional[str]) -> Any:
        """Helper to create either a standard OpenAI (Foundry Serverless) or AzureOpenAI client."""
        if not endpoint:
            return None
            
        if settings.api_version == "v1" or "/v1" in endpoint:
            base_url = endpoint.rstrip('/')
            if not base_url.endswith("/openai/v1") and not base_url.endswith("/v1"):
                # If it's a foundry project URL and lacks v1, append standard Foundry v1 path
                base_url += "/openai/v1" if "projects" in base_url else "/v1"
                
            return AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                default_headers={"api-key": api_key} if api_key else {}
            )
        else:
            return AsyncAzureOpenAI(
                api_key=api_key,
                api_version=settings.api_version,
                azure_endpoint=endpoint
            )

    async def initialize(self):
        """Asynchronously initialize the clients based on available configuration."""
        if self.chat_client is not None:
            return

        if settings.project_connection_string:
            credential = DefaultAzureCredential()
            self.project_client = AIProjectClient.from_connection_string(
                credential=credential,
                conn_str=settings.project_connection_string,
            )
            self.chat_client = await self.project_client.inference.get_azure_openai_client(
                api_version=settings.api_version
            )
            # Default everything to the project client if specific endpoints aren't provided
            self.embedding_client = self.chat_client
            self.image_client = self.chat_client
        else:
            # Main Chat Client
            self.chat_client = self._create_openai_client(
                settings.azure_openai_endpoint, 
                settings.azure_openai_api_key
            )
            
            # Sub-clients (fallback to chat client if specific endpoint isn't provided)
            self.embedding_client = self._create_openai_client(
                settings.embedding_endpoint, settings.embedding_api_key
            ) or self.chat_client
            
            self.image_client = self._create_openai_client(
                settings.image_endpoint, settings.image_api_key
            ) or self.chat_client

    async def close(self):
        """Cleanly close underlying HTTP clients."""
        if self.project_client:
            await self.project_client.close()
        elif self.chat_client:
            await self.chat_client.close()
            if self.embedding_client and self.embedding_client != self.chat_client:
                await self.embedding_client.close()
            if self.image_client and self.image_client != self.chat_client:
                await self.image_client.close()

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    async def generate_lore(self, prompt: str, system_prompt: str = "You are a helpful assistant.", temperature: float = 0.7) -> str:
        async with self.limiter:
            await self.initialize()
            response = await self.chat_client.chat.completions.create(
                model=settings.bulk_lore_deployment_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                temperature=temperature,
                max_completion_tokens=4000
            )
            return response.choices[0].message.content

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=20), reraise=True)
    async def synthesize_reasoning(self, prompt: str, system_prompt: str) -> str:
        async with self.limiter:
            await self.initialize()
            response = await self.chat_client.chat.completions.create(
                model=settings.reasoning_deployment_name,
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}],
                temperature=0.1
            )
            return response.choices[0].message.content

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def generate_embedding(self, text: str) -> List[float]:
        async with self.limiter:
            await self.initialize()
            response = await self.embedding_client.embeddings.create(
                model=settings.embedding_deployment_name,
                input=text
            )
            return response.data[0].embedding

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def generate_image(self, prompt: str) -> str:
        async with self.limiter:
            await self.initialize()
            response = await self.image_client.images.generate(
                model=settings.image_generation_deployment,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            return response.data[0].url

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
    async def rerank(self, query: str, documents: List[str]) -> List[Dict[str, Any]]:
        """Hits the Cohere Rerank endpoint directly using httpx (Azure Foundry standard format)."""
        async with self.limiter:
            await self.initialize()
            endpoint = settings.rerank_endpoint or settings.azure_openai_endpoint
            api_key = settings.rerank_api_key or settings.azure_openai_api_key
            
            # Ensure proper v1/rerank route for Azure Cohere deployments
            url = endpoint.rstrip('/')
            if not url.endswith("/v1/rerank"):
                url += "/v1/rerank" if url.endswith("/v1") else "/v1/rerank"
                
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "api-key": api_key
            }
            payload = {
                "query": query,
                "documents": documents,
                "top_n": len(documents)
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                return response.json().get("results", [])
