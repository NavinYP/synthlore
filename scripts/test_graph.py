import os
import sys
import json
import networkx as nx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.graph.config import WorldConfig
from src.graph.generator import KnowledgeGraphGenerator

def run_test():
    config = WorldConfig.default_arcane_industrial()
    generator = KnowledgeGraphGenerator(config)
    G = generator.generate(num_nodes=20)
    
    data = nx.node_link_data(G)
    out_dir = os.path.expanduser("~/.gemini/antigravity/brain/980fc4a1-a925-4fa0-8265-5d532a40b50e/scratch")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "sample_graph.json")
    with open(out_file, "w") as f:
        json.dump(data, f, indent=2)
        
    print(f"✅ Generated 5-node sample graph to: {out_file}")
    for u, v, data in G.edges(data=True):
        print(f"Edge: {G.nodes[u]['name']} -[{data['relation']}]-> {G.nodes[v]['name']}")

if __name__ == "__main__":
    run_test()
