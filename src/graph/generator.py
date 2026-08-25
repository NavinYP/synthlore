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
            node_type_obj = random.choice(self.config.node_types)
            entity_type = node_type_obj.name
            
            # Add some basic temporal/metadata attributes
            established_year = random.randint(self.config.start_year, self.config.end_year)
            
            node_data = {
                "type": entity_type,
                "established": established_year,
                "name": f"{entity_type}-{str(uuid.uuid4())[:8]}",
                "active": random.choice([True, True, False])
            }
            
            # Populate specific properties defined in the config
            for prop in node_type_obj.properties:
                if prop not in node_data:
                    if prop in ["capacity", "throughput", "yield", "radiation", "debt", "bandwidth", "level"]:
                        node_data[prop] = random.randint(10, 999)
                    else:
                        node_data[prop] = f"UNKNOWN_{prop.upper()}"
            
            self.graph.add_node(node_id, **node_data)
            nodes.append((node_id, entity_type))

        # 2. Generate Edges (strictly adhering to config rules)
        # We need to map available types to node lists for fast lookup
        nodes_by_type = {nt.name: [] for nt in self.config.node_types}
        for nid, etype in nodes:
            if etype in nodes_by_type:
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

        self.inject_contradictions()
        return self.graph

    def inject_contradictions(self):
        """Injects conflicting properties into ~10% of nodes to serve as unreliable narrators for Track 1C."""
        target_count = max(1, int(self.graph.number_of_nodes() * 0.1))
        nodes_to_corrupt = random.sample(list(self.graph.nodes()), target_count)
        
        for nid in nodes_to_corrupt:
            # Create a conflicting property record
            node_data = self.graph.nodes[nid]
            established_fake = random.randint(self.config.start_year, self.config.end_year)
            while established_fake == node_data["established"]:
                established_fake = random.randint(self.config.start_year, self.config.end_year)
                
            active_fake = not node_data["active"]
            
            # Store it under 'contradictions' so the compiler can selectively weave it in
            self.graph.nodes[nid]["contradictions"] = {
                "established": established_fake,
                "active": active_fake,
                "narrative": f"There are conflicting rumors that {node_data['name']} was actually established in {established_fake} and is currently {'active' if active_fake else 'defunct'}."
            }

    def get_graph_stats(self) -> Dict[str, Any]:
        """Returns basic statistics of the generated graph."""
        return {
            "num_nodes": self.graph.number_of_nodes(),
            "num_edges": self.graph.number_of_edges(),
            "setting": self.config.setting_name,
            "is_directed": self.graph.is_directed()
        }
