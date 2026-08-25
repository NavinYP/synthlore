import asyncio
import time
from src.generation.llm_client import UnifiedAIClient
from src.settings import settings

async def generate_image(llm, prompt, i, sem):
    async with sem:
        print(f"[{i}] Starting image generation...")
        t0 = time.time()
        try:
            response = await llm.image_client.images.generate(
                model=settings.image_generation_deployment,
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            t = time.time() - t0
            print(f"[{i}] ✅ Done in {t:.2f}s")
            return t
        except Exception as e:
            print(f"[{i}] ❌ Failed: {e}")
            return None

async def main():
    print("Testing Parallel Image Generation...")
    llm = UnifiedAIClient()
    await llm.initialize()
    
    # Allow up to 3 concurrent requests
    sem = asyncio.Semaphore(3)
    
    prompts = [
        "A chalk sketch of an arcane gear.",
        "A blueprint of a steam-powered dispatch hub.",
        "A rough sketch of a guild overseer's ledger."
    ]
    
    start_time = time.time()
    tasks = [generate_image(llm, p, i, sem) for i, p in enumerate(prompts)]
    results = await asyncio.gather(*tasks)
    total_time = time.time() - start_time
    
    print("\n" + "="*40)
    print(f"Total time for {len(prompts)} parallel images: {total_time:.2f}s")
    valid_results = [r for r in results if r is not None]
    if valid_results:
        avg = sum(valid_results) / len(valid_results)
        print(f"Average time per image: {avg:.2f}s")
    print("="*40)

if __name__ == "__main__":
    asyncio.run(main())
