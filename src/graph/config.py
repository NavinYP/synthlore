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

    @classmethod
    def default_cyberpunk_corporate(cls):
        return cls(
            setting_name="Cyberpunk Corporate Syndicate",
            tone="Neon-lit, hyper-capitalist, cynical, high-tech low-life, surveillance state.",
            factions=["OmniCorp", "Neon Syndicate", "NetRunners", "The Board"],
            node_types=[
                NodeType(name="Operative", properties=["alias", "cyberware", "faction", "debt"]),
                NodeType(name="Mainframe", properties=["designation", "security_level", "status", "location"]),
                NodeType(name="Data Hub", properties=["sector", "bandwidth", "manager"]),
                NodeType(name="Syndicate", properties=["name", "specialty", "influence"]),
                NodeType(name="Executive", properties=["name", "clearance_level", "assigned_hub"]),
                NodeType(name="Biotech Lab", properties=["designation", "output_material", "hazards"]),
            ],
            edge_types=[
                EdgeType(name="CONTRACTED_TO", source_type="Operative", target_type="Data Hub", description="Employment"),
                EdgeType(name="HACKS", source_type="Operative", target_type="Mainframe", description="Intrusion duty"),
                EdgeType(name="ROUTES_THROUGH", source_type="Data Hub", target_type="Mainframe", description="Data dependency"),
                EdgeType(name="AFFILIATED_WITH", source_type="Operative", target_type="Syndicate", description="Affiliation"),
                EdgeType(name="SUPPLIES", source_type="Biotech Lab", target_type="Data Hub", description="Material flow"),
                EdgeType(name="AUDITS", source_type="Executive", target_type="Data Hub", description="Inspection"),
            ],
            document_types=["Syndicate Ledger", "NetRunner Log", "System Crash Report", "Operative's Burner Cache", "Corporate Contract", "Termination Notice", "Bribe Record"],
            corpus_distribution=CorpusDistribution(
                image_injection_ratio=0.10,
                format_ratios={".pdf": 0.40, ".png": 0.20, ".docx": 0.20, ".txt": 0.20}
            ),
            start_year=2080,
            end_year=2120
        )

    @classmethod
    def default_deep_space_colony(cls):
        return cls(
            setting_name="Deep Space Mining Colony",
            tone="Isolated, claustrophobic, survival-focused, stark, utilitarian.",
            factions=["Terra-Corp", "Outer Rim Miners", "Station AI", "Smuggler Cartel"],
            node_types=[
                NodeType(name="Colonist", properties=["name", "specialty", "faction", "health"]),
                NodeType(name="Life Support Node", properties=["designation", "capacity", "status", "level"]),
                NodeType(name="Mining Sector", properties=["name", "yield", "manager"]),
                NodeType(name="Cartel", properties=["name", "contraband", "influence"]),
                NodeType(name="Commander", properties=["name", "clearance", "assigned_sector"]),
                NodeType(name="Ore Refinery", properties=["name", "output_material", "radiation"]),
            ],
            edge_types=[
                EdgeType(name="STATIONED_AT", source_type="Colonist", target_type="Mining Sector", description="Employment"),
                EdgeType(name="MAINTAINS", source_type="Colonist", target_type="Life Support Node", description="Technical duty"),
                EdgeType(name="OXYGEN_SUPPLY", source_type="Mining Sector", target_type="Life Support Node", description="Dependency"),
                EdgeType(name="OWES", source_type="Colonist", target_type="Cartel", description="Affiliation"),
                EdgeType(name="PROCESSES_FOR", source_type="Ore Refinery", target_type="Mining Sector", description="Material flow"),
                EdgeType(name="INSPECTS", source_type="Commander", target_type="Mining Sector", description="Inspection"),
            ],
            document_types=["Cargo Manifest", "Comms Intercept", "Life Support Log", "Contraband Ledger", "Colony Directive", "Incident Report", "Refinery Output"],
            corpus_distribution=CorpusDistribution(
                image_injection_ratio=0.10,
                format_ratios={".pdf": 0.40, ".png": 0.20, ".docx": 0.20, ".txt": 0.20}
            ),
            start_year=2310,
            end_year=2350
        )
