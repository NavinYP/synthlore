import asyncio
import json
import time
from src.generation.llm_client import UnifiedAIClient
from src.settings import settings

async def main():
    print("Testing Azure Batch API...")
    llm = UnifiedAIClient()
    await llm.initialize()
    
    batch_file_path = "batch_requests.jsonl"
    with open(batch_file_path, "w") as f:
        for i in range(3):
            req = {
                "custom_id": f"doc-{i}",
                "method": "POST",
                "url": "/chat/completions",
                "body": {
                    "model": settings.bulk_lore_deployment_name,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": f"Write a tiny 2 sentence story about robot {i}."}
                    ]
                }
            }
            f.write(json.dumps(req) + "\n")
            
    print("Uploading file to Azure...")
    try:
        file_obj = await llm.chat_client.files.create(
            file=open(batch_file_path, "rb"),
            purpose="batch"
        )
        print(f"File uploaded! ID: {file_obj.id}")
        
        print("Submitting Batch Job...")
        batch_job = await llm.chat_client.batches.create(
            input_file_id=file_obj.id,
            endpoint="/chat/completions",
            completion_window="24h"
        )
        print(f"Batch Job Created! ID: {batch_job.id}, Status: {batch_job.status}")
        
        # Don't poll indefinitely, just show it was successfully submitted
        print("Batch successfully submitted to Azure's async queue. It will complete within 24h.")
    except Exception as e:
        print("❌ Batch API Error:", e)

if __name__ == "__main__":
    asyncio.run(main())
