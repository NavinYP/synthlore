import asyncio
import os
import sys
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from openai import AsyncOpenAI

async def run_tests():
    api_key = settings.azure_openai_api_key
    
    # Test 1: Embeddings with Project Path
    print("Testing Embeddings with Project Path...")
    try:
        emb_client = AsyncOpenAI(
            api_key=api_key,
            base_url="https://codefest-ai-hub-eu2.services.ai.azure.com/api/projects/codefest-synth-data-eu2/openai/v1",
            default_headers={"api-key": api_key}
        )
        response = await emb_client.embeddings.create(
            model=settings.embedding_deployment_name,
            input="Test"
        )
        print("✅ Embeddings Success!")
    except Exception as e:
        print(f"❌ Embeddings Failed: {e}")

    # Test 2: Cohere Rerank with api-version
    print("\nTesting Cohere Rerank with api-version=2024-05-01-preview...")
    url = settings.rerank_endpoint + "?api-version=2024-05-01-preview"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "query": "What is a test?",
        "documents": ["A test is a trial.", "An apple."],
        "top_n": 2
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("✅ Cohere Success!")
        else:
            print(f"❌ Cohere Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    asyncio.run(run_tests())
