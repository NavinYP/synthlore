import json
import random
import networkx as nx
from typing import Dict, List, Any
from src.generation.llm_client import UnifiedAIClient

class QAGenerator:
    def __init__(self, llm_client: UnifiedAIClient, config_path: str):
        self.llm_client = llm_client
        with open(config_path, "r") as f:
            self.config = json.load(f)
            
    async def generate_question(self, G: nx.DiGraph, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """Generates a single question based on the loaded strategies."""
        # Weighted random choice of strategy
        weights = [s["weight"] for s in self.config["strategies"]]
        strategy = random.choices(self.config["strategies"], weights=weights, k=1)[0]
        reqs = strategy["requirements"]
        
        prompt = ""
        reasoning_path = []
        
        if reqs.get("needs_image"):
            # Find a node that has needs_image == true
            valid_nodes = [nid for nid, m in manifest.items() if m.get("needs_image")]
            if not valid_nodes:
                return {} # Fallback
            focal_node = random.choice(valid_nodes)
            node_name = G.nodes[focal_node]['name']
            reasoning_path = [node_name]
            prompt = f"Focal Entity: {node_name}\nProperties: {json.dumps(G.nodes[focal_node])}"
            
        elif reqs.get("path_length") == 2:
            # Find a 2-hop path A -> B -> C
            edges = list(G.edges())
            valid_paths = []
            for u, v in edges:
                for w in G.successors(v):
                    if u != w:
                        valid_paths.append((u, v, w))
            if not valid_paths:
                return {}
                
            u, v, w = random.choice(valid_paths)
            node_a = G.nodes[u]['name']
            node_b = G.nodes[v]['name']
            node_c = G.nodes[w]['name']
            reasoning_path = [node_a, node_b, node_c]
            
            prompt = f"Graph Path:\n1. {node_a} ({G.nodes[u]['type']}) -> [RELATES TO] -> {node_b} ({G.nodes[v]['type']})\n"
            prompt += f"2. {node_b} ({G.nodes[v]['type']}) -> [RELATES TO] -> {node_c} ({G.nodes[w]['type']})"
            
        elif reqs.get("path_length") == 1:
            # Pick a single edge/relationship
            edges = list(G.edges(data=True))
            if not edges:
                return {}
            u, v, data = random.choice(edges)
            node_a = G.nodes[u]['name']
            node_b = G.nodes[v]['name']
            reasoning_path = [node_a, node_b]
            prompt = f"Entity A: {node_a} ({json.dumps(G.nodes[u])})\nEntity B: {node_b} ({json.dumps(G.nodes[v])})\nRelationship: {data}"
        else:
            # Generic fallback
            n = random.choice(list(G.nodes()))
            node_name = G.nodes[n]['name']
            reasoning_path = [node_name]
            prompt = f"Entity: {node_name} Properties: {json.dumps(G.nodes[n])}"

        # Call the reasoning model
        system_prompt = strategy["system_prompt"]
        try:
            raw_response = await self.llm_client.synthesize_reasoning(prompt, system_prompt)
            # Strip markdown if present
            if raw_response.startswith("```json"):
                raw_response = raw_response.strip("```json").strip("```")
            elif raw_response.startswith("```"):
                raw_response = raw_response.strip("```")
                
            qa_pair = json.loads(raw_response.strip())
            
            # Ensure reasoning path matches our ground truth override
            qa_pair["reasoning_path"] = reasoning_path
            return qa_pair
        except Exception as e:
            print(f"Failed to parse or generate Q&A: {e}")
            return {}
