import asyncio
import os
import sys
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings

async def run_tests():
    api_key = settings.azure_openai_api_key
    url = "https://codefest-ai-hub-eu2.services.ai.azure.com/api/projects/codefest-synth-data-eu2/v1/embeddings?api-version=2024-05-01-preview"
    
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
        print(f"Test 3 (Inference API with api-version): {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    asyncio.run(run_tests())
