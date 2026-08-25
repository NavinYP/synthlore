import random
import uuid
import networkx as nx
from typing import Dict, Any, List
from src.graph.config import WorldConfig

class KnowledgeGraphGenerator:
    def __init__(self, config: WorldConfig):
        self.config = config
        self.graph = nx.DiGraph()

    def generate(self, num_nodes: int = 50) -> nx.DiGraph:
        """
        Generates a synthetic ground-truth knowledge graph based on the WorldConfig.
        """
        self.graph.clear()
        
        # 1. Generate Nodes
        nodes = []
        for _ in range(num_nodes):
            node_id = str(uuid.uuid4())
            entity_type = random.choice(self.config.entity_types)
            
            # Add some basic temporal/metadata attributes
            established_year = random.randint(self.config.start_year, self.config.end_year)
            
            node_data = {
                "type": entity_type,
                "established": established_year,
                "name": f"{entity_type}-{str(uuid.uuid4())[:8]}", # Dummy names for now
                "active": random.choice([True, True, False]) # 66% chance to be active
            }
            
            self.graph.add_node(node_id, **node_data)
            nodes.append((node_id, entity_type))

        # 2. Generate Edges (strictly adhering to config rules)
        # We need to map available types to node lists for fast lookup
        nodes_by_type = {etype: [] for etype in self.config.entity_types}
        for nid, etype in nodes:
            nodes_by_type[etype].append(nid)

        # Iterate over all nodes, try to create some out-edges based on allowed rules
        for node_id, entity_type in nodes:
            # Find allowed edge types where source matches this node's type
            allowed_out_edges = [edge for edge in self.config.edge_types if edge.source_type == entity_type]
            
            if not allowed_out_edges:
                continue

            # Randomly select a few edges to form
            num_edges_to_create = random.randint(1, 3)
            for _ in range(num_edges_to_create):
                edge_rule = random.choice(allowed_out_edges)
                target_candidates = nodes_by_type[edge_rule.target_type]
                
                if not target_candidates:
                    continue
                
                target_id = random.choice(target_candidates)
                
                # Prevent self-loops
                if target_id == node_id:
                    continue
                
                # Add the edge with some temporal context
                timestamp = random.randint(
                    self.graph.nodes[node_id]['established'], 
                    self.config.end_year
                )
                
                self.graph.add_edge(
                    node_id, 
                    target_id, 
                    relation=edge_rule.name,
                    timestamp=timestamp
                )

        return self.graph

    def get_graph_stats(self) -> Dict[str, Any]:
        """Returns basic statistics of the generated graph."""
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "setting": self.config.setting_name,
            "is_directed": self.graph.is_directed()
        }
