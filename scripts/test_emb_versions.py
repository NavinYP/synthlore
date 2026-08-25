import asyncio
import os
import sys
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings

async def run_tests():
    api_key = settings.azure_openai_api_key
    versions = ["2023-05-15", "2024-02-15-preview", "2024-06-01", "2024-10-21", "2024-12-01-preview", "2025-01-01-preview", "2026-01-01-preview"]
    for v in versions:
        url = f"https://codefest-ai-hub-eu2.services.ai.azure.com/api/projects/codefest-synth-data-eu2/v1/embeddings?api-version={v}"
        
        headers = {
            "api-key": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": "Test",
            "model": settings.embedding_deployment_name
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print(f"✅ Success with {v}!")
                return
            else:
                print(f"Failed {v}: {response.text}")

if __name__ == "__main__":
    asyncio.run(run_tests())
