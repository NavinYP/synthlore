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
                "name": self._generate_thematic_value("name", entity_type),
                "active": random.choice([True, True, False])
            }
            
            # Populate specific properties defined in the config
            for prop in node_type_obj.properties:
                if prop not in node_data:
                    if prop in ["capacity", "throughput", "yield", "radiation", "debt", "bandwidth", "level"]:
                        node_data[prop] = random.randint(10, 999)
                    elif prop == "faction":
                        node_data[prop] = random.choice(self.config.factions)
                    else:
                        node_data[prop] = self._generate_thematic_value(prop, entity_type)
            
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
                
                # World-Building Clustering Logic:
                # 80% of the time, try to connect to a node in the SAME faction or region.
                # 20% of the time, connect globally (spies, cross-faction trade, etc.)
                source_data = self.graph.nodes[node_id]
                local_candidates = [
                    t for t in target_candidates 
                    if self.graph.nodes[t].get("faction") == source_data.get("faction") 
                    or self.graph.nodes[t].get("region") == source_data.get("region")
                ]
                
                if local_candidates and random.random() < 0.8:
                    target_id = random.choice(local_candidates)
                else:
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

    def _generate_thematic_value(self, prop: str, entity_type: str) -> str:
        """Procedurally generates deep lore attributes based on the dynamic naming banks."""
        banks = self.config.naming_banks
        
        if prop == "name":
            if entity_type in ["Person", "Operative", "Colonist", "Commander", "Executive", "Overseer"]:
                return random.choice(banks.get("name_person", ["Unknown"])) + f" {random.randint(1,99)}"
            elif entity_type == "Historical Crisis":
                return random.choice(banks.get("name_crisis", ["Unknown Event"]))
            else:
                return random.choice(banks.get("name_facility", ["Unknown Facility"])) + f" {random.randint(100,999)}"
                
        elif prop in ["region", "location", "sector"]:
            return random.choice(banks.get("region", ["Unknown Region"]))
        elif prop in ["role", "manager"]:
            return random.choice(banks.get("role", ["Unknown Role"]))
        elif prop == "specialty":
            return random.choice(banks.get("specialty", ["Unknown Specialty"]))
        elif prop in ["clearance", "clearance_level", "security_level"]:
            return random.choice(banks.get("clearance", ["Unknown Clearance"]))
        elif prop == "secret":
            return random.choice(banks.get("secret", ["Unknown Secret"]))
        elif prop == "contraband":
            return random.choice(banks.get("contraband", ["Unknown Contraband"]))
        elif prop == "hazards":
            return random.choice(banks.get("hazards", ["Unknown Hazard"]))
        elif prop == "output_material":
            return random.choice(banks.get("material", ["Unknown Material"]))
        elif prop == "outcome":
            return random.choice(banks.get("outcome", ["Unknown Outcome"]))
        elif prop == "secret_truth":
            return random.choice(banks.get("secret_truth", ["Unknown Truth"]))
        elif prop == "casualty_rate":
            return str(random.randint(500, 50000))
            
        return f"Unknown_{prop}"
