import asyncio
import os
import sys
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from openai import AsyncOpenAI

async def run_tests():
    api_key = settings.azure_openai_api_key
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://codefest-ai-hub-eu2.services.ai.azure.com/api/projects/codefest-synth-data-eu2/openai/v1",
        default_headers={"api-key": api_key}
    )
    
    print("Testing text-embedding-3-large on chat endpoint...")
    try:
        await client.chat.completions.create(model="text-embedding-3-large", messages=[{"role":"user","content":"Hi"}])
    except Exception as e:
        print(f"Result: {e}")

if __name__ == "__main__":
    asyncio.run(run_tests())
