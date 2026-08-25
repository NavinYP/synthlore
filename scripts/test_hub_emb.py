import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from openai import AsyncOpenAI

async def run_tests():
    api_key = settings.azure_openai_api_key
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://codefest-ai-hub-eu2.services.ai.azure.com/openai/v1",
        default_headers={"api-key": api_key}
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
