import asyncio
import sys
import os

# Add root to python path to resolve src modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.settings import settings
from src.generation.llm_client import UnifiedAIClient

async def ping_deployment(client: UnifiedAIClient, deployment_name: str, test_type: str = "chat"):
    """Pings a specific deployment to check for 200 OK reachability."""
    print(f"Testing [{deployment_name}] endpoint ({test_type})...", end=" ", flush=True)
    try:
        if test_type == "chat":
            # Simple ping to chat completion endpoints (Bulk, Reasoning, Vision text check)
            response = await client.inference_client.chat.completions.create(
                model=deployment_name,
                messages=[{"role": "user", "content": "Ping. Respond with 'Pong'."}],
                max_completion_tokens=10
            )
            print(f"✅ Success! (Response: {response.choices[0].message.content.strip()})")
            
        elif test_type == "embedding":
            response = await client.inference_client.embeddings.create(
                model=deployment_name,
                input="Test embedding"
            )
            print(f"✅ Success! (Vector length: {len(response.data[0].embedding)})")
            
        elif test_type == "image":
            # Just test if the endpoint exists, it might fail on prompt rejection but 
            # we are mainly checking for 404/Authentication errors
            print("⚠️ Skipping direct image generation ping to save costs, but config is loaded.")
            
        return True
    except Exception as e:
        print(f"❌ Failed! Error: {e}")
        return False

async def run_smoke_test():
    print("="*50)
    print("🚀 SyntheticLore-Bench Smoke Test")
    print("="*50)
    
    # Check if we have credentials
    if not settings.project_connection_string and not settings.azure_openai_api_key:
        print("❌ CRITICAL: No credentials found. Did you fill out the .env file?")
        sys.exit(1)
        
    client = UnifiedAIClient()
    await client.initialize()
    
    print("\n[Endpoints to Test]")
    success_count = 0
    total_tests = 4
    
    success_count += await ping_deployment(client, settings.bulk_lore_deployment_name, "chat")
    success_count += await ping_deployment(client, settings.reasoning_deployment_name, "chat")
    success_count += await ping_deployment(client, settings.vision_deployment_name, "chat")
    success_count += await ping_deployment(client, settings.embedding_deployment_name, "embedding")
    
    print("\n" + "="*50)
    if success_count == total_tests:
        print("🎉 ALL SYSTEMS GO! All deployments are reachable.")
    else:
        print(f"⚠️ Warning: {success_count}/{total_tests} endpoints reachable. Check your Azure Foundry deployments/names.")
    
    await client.close()

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
