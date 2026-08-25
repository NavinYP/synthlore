import asyncio
import os
import sys
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings

async def run_tests():
    api_key = settings.azure_openai_api_key
    url = "https://codefest-ai-hub-eu2.services.ai.azure.com/api/projects/codefest-synth-data-eu2/openai/deployments/text-embedding-3-large/embeddings?api-version=2024-02-15-preview"
    
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "input": "Test"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        print(f"Test: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    asyncio.run(run_tests())
