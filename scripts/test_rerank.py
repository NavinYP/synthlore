import asyncio
import sys
import os
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings

async def test_versions():
    url = settings.azure_openai_endpoint.rstrip('/') + "/v1/rerank"
    headers = {
        "Authorization": f"Bearer {settings.azure_openai_api_key}",
        "api-key": settings.azure_openai_api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "query": "What is a test?",
        "documents": ["A test is a trial.", "An apple."],
        "model": settings.rerank_deployment_name
    }
    print(f"Testing {url} with model {settings.rerank_deployment_name}...")
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        print(response.status_code)
        print(response.text)

if __name__ == "__main__":
    asyncio.run(test_versions())
