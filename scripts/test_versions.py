import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from openai import AsyncAzureOpenAI

async def test_versions():
    versions = ["2023-05-15", "2024-02-15-preview", "2024-06-01", "2024-10-21", "2024-12-01-preview", "2025-01-01-preview", "2026-01-01-preview"]
    for v in versions:
        try:
            client = AsyncAzureOpenAI(
                api_key=settings.azure_openai_api_key,
                api_version=v,
                azure_endpoint=settings.azure_openai_endpoint
            )
            print(f"Testing {v}...")
            response = await client.chat.completions.create(
                model=settings.bulk_lore_deployment_name,
                messages=[{"role": "user", "content": "Ping."}],
                max_tokens=5
            )
            print(f"✅ Success with {v}!")
            return
        except Exception as e:
            print(f"Failed {v}: {e}")

if __name__ == "__main__":
    asyncio.run(test_versions())
