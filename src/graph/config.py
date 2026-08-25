from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class EdgeType(BaseModel):
    name: str
    source_type: str
    target_type: str
    description: Optional[str] = None

class WorldConfig(BaseModel):
    """Configuration for the aesthetic and structural rules of the generated world."""
    setting_name: str = Field(description="Name of the world setting (e.g. 'Arcane Industrial')")
    entity_types: List[str] = Field(description="Allowed node types (e.g. ['Guild', 'Aether-Reactor'])")
    edge_types: List[EdgeType] = Field(description="Allowed relationships between entities")
    start_year: int = Field(default=1800, description="Starting year for temporal metadata")
    end_year: int = Field(default=1900, description="Ending year for temporal metadata")
    document_types: List[str] = Field(default_factory=lambda: ["Technical Manual", "Personal Letter", "Official Contract", "Maintenance Log", "Audit Report", "Blueprint Annotation"], description="Types of documents to generate")
    
    @classmethod
    def default_arcane_industrial(cls):
        return cls(
            setting_name="Arcane Industrial",
            entity_types=[
                "Guild", 
                "Aether-Reactor", 
                "Overseer", 
                "Dispatch Hub", 
                "Foundry",
                "Automaton"
            ],
            edge_types=[
                EdgeType(name="MANUFACTURES", source_type="Guild", target_type="Aether-Reactor", description="Guild builds reactors"),
                EdgeType(name="REPORTS_TO", source_type="Overseer", target_type="Guild", description="Chain of command"),
                EdgeType(name="SUPPLIES", source_type="Foundry", target_type="Guild", description="Raw material supply"),
                EdgeType(name="REGULATES", source_type="Dispatch Hub", target_type="Aether-Reactor", description="Operational control"),
                EdgeType(name="MAINTAINS", source_type="Automaton", target_type="Aether-Reactor", description="Upkeep"),
                EdgeType(name="BELONGS_TO", source_type="Automaton", target_type="Guild", description="Ownership"),
                EdgeType(name="AUDITS", source_type="Overseer", target_type="Dispatch Hub", description="Inspection"),
            ],
            document_types=["Guild Ledger", "Dispatcher Log", "Maintenance Report", "Smuggler's Diary", "Official Contract", "Letter of Grievance", "Procurement Order"],
            start_year=1840,
            end_year=1899
        )
