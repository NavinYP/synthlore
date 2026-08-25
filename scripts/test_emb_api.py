import asyncio
import os
import sys
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings

async def run_tests():
    api_key = settings.azure_openai_api_key
    versions = ["2023-05-15", "2024-02-15-preview", "2024-06-01", "2024-10-21", "2024-08-01-preview", "2024-12-01-preview"]
    for v in versions:
        url = f"https://codefest-ai-hub-eu2.services.ai.azure.com/api/projects/codefest-synth-data-eu2/openai/deployments/text-embedding-3-large/embeddings?api-version={v}"
        
        headers = {
            "api-key": api_key,
            "Content-Type": "application/json"
        }
        payload = {
            "input": "Test"
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"✅ Route works with {v}! Response: {response.status_code}")
                return
            else:
                print(f"Failed {v}: {response.text}")

if __name__ == "__main__":
    asyncio.run(run_tests())
