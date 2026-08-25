import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from openai import AsyncOpenAI

async def test_versions():
    url = settings.azure_openai_endpoint.rstrip('/') + "/openai/v1"
    client = AsyncOpenAI(
        api_key=settings.azure_openai_api_key,
        base_url=url,
        default_headers={"api-key": settings.azure_openai_api_key} # Azure sometimes needs api-key header instead of Authorization: Bearer
    )
    print(f"Testing AsyncOpenAI with base_url={url}...")
    try:
        response = await client.chat.completions.create(
            model=settings.bulk_lore_deployment_name,
            messages=[{"role": "user", "content": "Ping."}],
            max_tokens=5
        )
        print("✅ Success! Response:", response.choices[0].message.content)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_versions())
