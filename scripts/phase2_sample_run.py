import random
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph.config import WorldConfig
from src.graph.generator import KnowledgeGraphGenerator
from src.generation.llm_client import UnifiedAIClient
from src.generation.document_compiler import DocumentCompiler

async def run_samples():
    print("="*50)
    print("🔮 Phase 2: Generating 5 Mock Documents for Manual Review")
    print("="*50)
    
    # 1. Init Config & Graph
    config = WorldConfig.default_arcane_industrial()
    generator = KnowledgeGraphGenerator(config)
    print("\n1. Generating synthetic knowledge graph (20 nodes)...")
    G = generator.generate(num_nodes=20)
    
    # 2. Init LLM Client & Compiler
    llm_client = UnifiedAIClient()
    await llm_client.initialize()
    compiler = DocumentCompiler(llm_client, config)
    
    # 3. Select 5 Target Nodes
    target_nodes = list(G.nodes)[:5]
    print(f"\n2. Selected focal nodes for compilation: {target_nodes}")
    
    # 4. Create Output Directory
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output", "samples")
    os.makedirs(out_dir, exist_ok=True)
    
    # Save the ground-truth graph for verification
    import networkx as nx
    import json
    graph_path = os.path.join(out_dir, "ground_truth_graph.json")
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(nx.node_link_data(G), f, indent=2)
    print(f"      ✅ Saved ground-truth graph to {graph_path}")
    
    # 5. Compile Documents
    print("\n3. Calling Azure Foundry (gpt-5.6-luna) to compile documents...")
    for i, node_id in enumerate(target_nodes):
        node_name = G.nodes[node_id]['name']
        print(f"   [{i+1}/5] Compiling document for {node_name}...")
        
        # Save the exact context string used for the prompt
        context = compiler.extract_subgraph_context(G, node_id)
        ctx_path = os.path.join(out_dir, f"{node_name}_CONTEXT.txt")
        with open(ctx_path, "w", encoding="utf-8") as f:
            f.write(context)
            
        # Generate and save the document
        doc_type = random.choice(config.document_types)
        print(f"      📝 Format: {doc_type}")
        doc_content = await compiler.compile_document(G, node_id, doc_type=doc_type)
        
        out_path = os.path.join(out_dir, f"{node_name}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(doc_content)
        
        print(f"      ✅ Saved to {out_path}")
        
    await llm_client.close()
    
    print("\n" + "="*50)
    print(f"🎉 SUCCESS! 5 sample documents generated in: {out_dir}")
    print("⚠️ PLEASE MANUALLY REVIEW THESE FILES BEFORE BULK GENERATION.")

if __name__ == "__main__":
    asyncio.run(run_samples())
