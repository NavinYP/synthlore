import asyncio
import os
import sys
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.generation.llm_client import UnifiedAIClient
from src.settings import settings

async def test_image():
    client = UnifiedAIClient()
    await client.initialize()
    print("Testing gpt-image-2 text generation...")
    
    prompt = "A pristine corporate bar chart showing a 14% drop in efficiency, with the exact text '14% DROP' clearly written in the chart. Typography must be highly legible."
    
    try:
        response = await client.image_client.images.generate(
            model=settings.image_generation_deployment,
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        img_b64 = response.data[0].b64_json
        with open("test_gpt_image_text.png", "wb") as fh:
            fh.write(base64.b64decode(img_b64))
        print("Saved to test_gpt_image_text.png")
    except Exception as e:
        print(f"Failed: {e}")
        
if __name__ == "__main__":
    asyncio.run(test_image())
