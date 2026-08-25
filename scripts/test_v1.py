import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from openai import AsyncAzureOpenAI

async def test_versions():
    client = AsyncAzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version="v1",
        azure_endpoint=settings.azure_openai_endpoint
    )
    print("Testing api_version='v1'...")
    try:
        response = await client.chat.completions.create(
            model=settings.bulk_lore_deployment_name,
            messages=[{"role": "user", "content": "Ping."}],
            max_tokens=5
        )
        print("✅ Success!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_versions())
