import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.settings import settings
from src.generation.llm_client import UnifiedAIClient

async def test_versions():
    client = UnifiedAIClient()
    await client.initialize()
    try:
        response = await client.chat_client.chat.completions.create(
            model="fake-model-123",
            messages=[{"role": "user", "content": "Ping."}],
            max_completion_tokens=5
        )
        print("✅ Success!")
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_versions())
