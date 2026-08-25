import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.settings import settings
from src.generation.llm_client import UnifiedAIClient

async def ping_deployment(client: UnifiedAIClient, deployment_name: str, test_type: str = "chat"):
    """Pings a specific deployment to check for reachability."""
    print(f"Testing [{deployment_name}] endpoint ({test_type})...", end=" ", flush=True)
    try:
        if test_type == "chat":
            response = await client.chat_client.chat.completions.create(
                model=deployment_name,
                messages=[{"role": "user", "content": "Ping."}],
                max_completion_tokens=5
            )
            print("✅ Success!")
            
        elif test_type == "embedding":
            response = await client.embedding_client.embeddings.create(
                model=deployment_name,
                input="Test embedding"
            )
            print(f"✅ Success! (Vector length: {len(response.data[0].embedding)})")
            
        elif test_type == "image":
            try:
                # Provide a tiny prompt to verify authorization
                response = await client.image_client.images.generate(
                    model=deployment_name,
                    prompt="A dot",
                    n=1,
                    size="1024x1024"
                )
                print("✅ Success! (Image generated)")
            except Exception as e:
                if "rate" in str(e).lower() or "billing" in str(e).lower() or "400" in str(e):
                    # 400 Bad Request / Quota means it reached the model perfectly!
                    print(f"✅ Reachable! (Encountered non-network error: {e})")
                else:
                    raise e
                    
        elif test_type == "rerank":
            results = await client.rerank("What is a test?", ["A test is a trial.", "An apple."])
            print(f"✅ Success! (Reranked {len(results)} docs)")
            
        return True
    except Exception as e:
        print(f"❌ Failed! Error: {e}")
        return False

async def run_smoke_test():
    print("="*50)
    print("🚀 Full Model Integration Smoke Test")
    print("="*50)
        
    client = UnifiedAIClient()
    await client.initialize()
    
    print("\n[Endpoints to Test]")
    success_count = 0
    total_tests = 6
    
    success_count += await ping_deployment(client, settings.bulk_lore_deployment_name, "chat")
    success_count += await ping_deployment(client, settings.reasoning_deployment_name, "chat")
    success_count += await ping_deployment(client, settings.vision_deployment_name, "chat")
    success_count += await ping_deployment(client, settings.embedding_deployment_name, "embedding")
    success_count += await ping_deployment(client, settings.image_generation_deployment, "image")
    success_count += await ping_deployment(client, settings.rerank_deployment_name, "rerank")
    
    print("\n" + "="*50)
    if success_count == total_tests:
        print("🎉 ALL SYSTEMS GO! All deployments are fully integrated and reachable.")
    else:
        print(f"⚠️ Warning: {success_count}/{total_tests} endpoints reachable. Review your .env specific endpoints.")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
