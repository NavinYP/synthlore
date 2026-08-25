from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class NodeType:
    name: str
    properties: List[str]

@dataclass
class EdgeType:
    name: str
    source_type: str
    target_type: str
    description: str

@dataclass
class CorpusDistribution:
    image_injection_ratio: float
    format_ratios: Dict[str, float]

@dataclass
class WorldConfig:
    setting_name: str
    tone: str
    factions: List[str]
    node_types: List[NodeType]
    edge_types: List[EdgeType]
    document_types: List[str]
    corpus_distribution: CorpusDistribution
    start_year: int
    end_year: int

    @classmethod
    def default_arcane_industrial(cls):
        return cls(
            setting_name="Arcane Industrial",
            tone="Grim, bureaucratic, soot-stained, bureaucratic intrigue.",
            factions=["The Iron Guild", "Aether Syndicate", "Ministry of Compliance", "The Smugglers"],
            node_types=[
                NodeType(name="Person", properties=["name", "role", "faction", "secret"]),
                NodeType(name="Aether-Reactor", properties=["name", "capacity", "status", "location"]),
                NodeType(name="Dispatch Hub", properties=["name", "region", "throughput", "manager"]),
                NodeType(name="Guild", properties=["name", "specialty", "influence"]),
                NodeType(name="Overseer", properties=["name", "clearance_level", "assigned_hub"]),
                NodeType(name="Foundry", properties=["name", "output_material", "hazards"]),
            ],
            edge_types=[
                EdgeType(name="WORKS_AT", source_type="Person", target_type="Dispatch Hub", description="Employment"),
                EdgeType(name="MAINTAINS", source_type="Person", target_type="Aether-Reactor", description="Technical duty"),
                EdgeType(name="POWERED_BY", source_type="Dispatch Hub", target_type="Aether-Reactor", description="Energy dependency"),
                EdgeType(name="BELONGS_TO", source_type="Person", target_type="Guild", description="Affiliation"),
                EdgeType(name="SUPPLIES", source_type="Foundry", target_type="Dispatch Hub", description="Material flow"),
                EdgeType(name="AUDITS", source_type="Overseer", target_type="Dispatch Hub", description="Inspection"),
            ],
            document_types=["Guild Ledger", "Dispatcher Log", "Maintenance Report", "Smuggler's Diary", "Official Contract", "Letter of Grievance", "Procurement Order"],
            corpus_distribution=CorpusDistribution(
                image_injection_ratio=0.10, # Reduced to 10%
                format_ratios={
                    ".pdf": 0.40,
                    ".png": 0.20,
                    ".docx": 0.20,
                    ".txt": 0.20
                }
            ),
            start_year=1840,
            end_year=1899
        )
