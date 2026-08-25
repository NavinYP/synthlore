import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from openai import AsyncAzureOpenAI

async def run_tests():
    api_key = settings.azure_openai_api_key
    client = AsyncAzureOpenAI(
        api_key=api_key,
        api_version="2024-02-15-preview",
        azure_endpoint=settings.azure_openai_endpoint
    )
    try:
        response = await client.embeddings.create(
            model=settings.embedding_deployment_name,
            input="Test"
        )
        print(f"✅ Success! Vector size: {len(response.data[0].embedding)}")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
