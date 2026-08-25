import os
import sys
import json
import asyncio
import argparse
from tqdm.asyncio import tqdm
import networkx as nx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.generation.llm_client import UnifiedAIClient
from src.evaluation.qa_generator import QAGenerator

async def main():
    parser = argparse.ArgumentParser(description="Generate Q&A Benchmark from Corpus Graph")
    parser.add_argument("--corpus_dir", required=True, help="Path to the generated corpus directory containing ground_truth_graph.json")
    parser.add_argument("--config", required=True, help="Path to the benchmark profile JSON config")
    parser.add_argument("--num_questions", type=int, default=10, help="Number of questions to generate")
    args = parser.parse_args()

    corpus_dir = os.path.abspath(args.corpus_dir)
    graph_path = os.path.join(corpus_dir, "ground_truth_graph.json")
    manifest_path = os.path.join(corpus_dir, "manifest.json")

    if not os.path.exists(graph_path) or not os.path.exists(manifest_path):
        print(f"❌ Error: Required files not found in {corpus_dir}")
        return

    print("Loading Graph and Manifest...")
    with open(graph_path, "r") as f:
        data = json.load(f)
        G = nx.node_link_graph(data)
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    print("Initializing LLM Client and QA Generator...")
    llm_client = UnifiedAIClient()
    await llm_client.initialize()
    
    qa_gen = QAGenerator(llm_client, args.config)
    
    print(f"Generating {args.num_questions} Questions using Configuration Profile...")
    
    benchmark = []
    
    # We shouldn't execute all reasoning tasks perfectly parallel if using o3 (rate limits are low)
    # We'll do it sequentially for the sample to be safe, or with a very small semaphore
    sem = asyncio.Semaphore(2)
    
    async def generate_single():
        async with sem:
            return await qa_gen.generate_question(G, manifest)
            
    tasks = [asyncio.create_task(generate_single()) for _ in range(args.num_questions)]
    
    for coro in tqdm.as_completed(tasks, total=len(tasks), desc="Synthesizing Q&A"):
        result = await coro
        if result:
            benchmark.append(result)
            
    out_path = os.path.join(corpus_dir, "benchmark_qa.json")
    with open(out_path, "w") as f:
        json.dump(benchmark, f, indent=2)
        
    print(f"\n✅ Benchmark generation complete! Saved to {out_path}")
    await llm_client.close()

if __name__ == "__main__":
    asyncio.run(main())
