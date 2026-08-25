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
    document_structures: List[str]
    naming_banks: Dict[str, List[str]]
    corpus_distribution: CorpusDistribution
    start_year: int
    end_year: int

    @classmethod
    def default_arcane_industrial(cls):
        return cls(
            setting_name="Arcane Industrial",
            tone="Grim, politically complex, steeped in betrayal, ancient grudges, and bureaucratic warfare. Factions vie for power over failing magical infrastructure, similar to the brutal political maneuvering of ASOIAF or Dune.",
            factions=["The Iron Guild", "Aether Syndicate", "Ministry of Compliance", "The Smuggler Cartels", "The Sovereign House"],
            node_types=[
                NodeType(name="Person", properties=["name", "role", "faction", "secret"]),
                NodeType(name="Aether-Reactor", properties=["name", "capacity", "status", "location"]),
                NodeType(name="Dispatch Hub", properties=["name", "region", "throughput", "manager"]),
                NodeType(name="Guild", properties=["name", "specialty", "influence"]),
                NodeType(name="Overseer", properties=["name", "clearance_level", "assigned_hub"]),
                NodeType(name="Foundry", properties=["name", "output_material", "hazards"]),
                NodeType(name="Historical Crisis", properties=["name", "casualty_rate", "outcome", "secret_truth"])
            ],
            edge_types=[
                EdgeType(name="WORKS_AT", source_type="Person", target_type="Dispatch Hub", description="Employment"),
                EdgeType(name="MAINTAINS", source_type="Person", target_type="Aether-Reactor", description="Technical duty"),
                EdgeType(name="POWERED_BY", source_type="Dispatch Hub", target_type="Aether-Reactor", description="Energy dependency"),
                EdgeType(name="BELONGS_TO", source_type="Person", target_type="Guild", description="Affiliation"),
                EdgeType(name="SUPPLIES", source_type="Foundry", target_type="Dispatch Hub", description="Material flow"),
                EdgeType(name="AUDITS", source_type="Overseer", target_type="Dispatch Hub", description="Inspection"),
                EdgeType(name="ORCHESTRATED", source_type="Person", target_type="Historical Crisis", description="Secretly caused the event"),
                EdgeType(name="DEVASTATED_BY", source_type="Dispatch Hub", target_type="Historical Crisis", description="Suffered during the event"),
                EdgeType(name="PROFIT_FROM", source_type="Guild", target_type="Historical Crisis", description="Capitalized on the tragedy")
            ],
            document_types=["Guild Ledger", "Dispatcher Log", "Maintenance Report", "Smuggler's Diary", "Official Contract", "Letter of Grievance", "Procurement Order", "Heretical Pamphlet", "Inquisitorial Transcript", "Alchemical Recipe"],
            document_structures=[
                "Format strictly as a raw dialogue transcript with SPEAKER labels and [BRACKETED] audio descriptions (e.g., [Static], [Sighs]).",
                "Format as a fragmented, deeply personal, and paranoid first-person narrative. Use erratic pacing.",
                "Format as passionate, zealous, or heretical prose. Use rhetorical questions, capitalization for emphasis, and grand allegories.",
                "Format as formal correspondence with a Salutation, Body, and Sign-off. Tone should be politically tense or aggressively bureaucratic.",
                "Format primarily as a dry, clinical table or bulleted list of items, interspersed with terse, cold annotations.",
                "Format as a frantically scribbled warning, encoded with metaphors, trying to bypass guild censors."
            ],
            naming_banks={
                "name_person": ["Silas", "Elara", "Kaelen", "Nyx", "Orion", "Jax", "Vex", "Cipher", "Thorne", "Valeria", "Darius", "Lysander", "Seraphina", "Rook", "Ghost"],
                "name_facility": ["Core-A", "Station-9", "Void-Hub", "Iron-Spire", "Nexus-Prime", "The Crucible", "Blacksite Omega", "Echo-Base", "Sector 7G"],
                "name_crisis": ["The Brass Blight", "The Cinder Mutiny", "The Great Schism", "The Void-Collapse", "The Silence of Sector 4", "The Blood-Tithe Rebellion"],
                "region": ["The Undercity", "Sector 4", "Outer Rim", "The Spire", "Sub-level 9", "The Wastes", "Neo-District", "Abyss-Trench", "The High Halls"],
                "role": ["Enforcer", "Smuggler", "Alchemist", "Netrunner", "Engineer", "Arch-Duke", "Overseer", "Scrapper", "Inquisitor", "Fixer"],
                "specialty": ["Void-tech", "Bio-engineering", "Dark Magic", "Cybernetics", "Contraband", "Heavy Artillery", "Espionage", "Quantum Cryptography"],
                "clearance": ["Omega-Level", "Alpha-Priority", "Beta-Standard", "Level 1", "Level 5", "Black-Op", "Unregistered"],
                "secret": ["Planning a coup", "Embezzling funds", "Working for a rival faction", "Hiding an AI fragment", "Infected with a parasite", "Seeking revenge"],
                "contraband": ["Spice", "Red-Lyrium", "Cyber-stims", "Void-Cores", "Unlicensed Cyberware", "Stolen Blueprints", "Aether-dust"],
                "hazards": ["Toxic Leak", "Radiation", "Warp-Anomaly", "Rogue AI", "Structural Collapse", "Bio-hazard", "Temporal Shift"],
                "material": ["Adamantine", "Plasteel", "Aether-dust", "Dark-matter", "Promethium", "Synth-blood", "Carbon-nanotubes"],
                "outcome": ["Quelled by military force", "Resulted in catastrophic structural failure", "Covered up by the Ministry", "Led to the exile of the instigators", "Still ongoing in the lower sectors"],
                "secret_truth": ["It was an inside job by the Overseers", "An ancient entity was awakened", "The official casualty count was divided by ten", "The rebellion was funded by a rival Guild"]
            },
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
            document_types=["Syndicate Ledger", "NetRunner Log", "System Crash Report", "Operative's Burner Cache", "Corporate Contract", "Termination Notice", "Bribe Record", "Hacker Manifesto", "Encrypted Audio Transcript", "Neural-link Dump"],
            document_structures=[
                "Format as a corrupted neural-dump with HEX strings, broken HTML tags, and paranoid thoughts slipping into the data.",
                "Format as a highly redacted corporate executive summary. Black out key names, leave brutal subtext.",
                "Format as a frantic, glitching terminal chat log between anonymous hackers (Handle A and Handle B).",
                "Format as an underground anti-corp manifesto calling for violence against the synthetics.",
                "Format as a clinical, horrifyingly casual autopsy or bio-harvesting report."
            ],
            naming_banks={
                "name_person": ["Zero", "Glitch", "Ripper", "Neon", "Cortez", "Silver", "Kira", "Dex", "V", "Chrome", "Akira", "Shin", "Raven"],
                "name_facility": ["DataVault 7", "Babel-Tower", "Synapse-Hub", "Blacksite Echo", "Corp-Spire", "Neon-Alley Clinic", "The Grid"],
                "name_crisis": ["The Y2K9 Crash", "The Chrome Rebellion", "The Great Blackout", "Synapse-Plague", "The Neon Purge"],
                "region": ["Neo-Kowloon", "Sector 7", "The Slums", "High-Orbit Corporate", "The Data Wastes", "Under-city"],
                "role": ["Netrunner", "Corpo", "Fixer", "Ripperdoc", "Mercenary", "Executive", "Hacker", "Synth"],
                "specialty": ["Cybernetics", "ICE-Breaker", "Assassination", "Data-Theft", "Smuggling", "Neuro-toxins"],
                "clearance": ["Level 1", "Level 9", "Board Member", "Restricted", "Black-Op", "Unregistered"],
                "secret": ["Selling data to rivals", "Is secretly an AI", "Has a lethal neural virus", "Planning to crash the grid"],
                "contraband": ["Neural-stims", "Black-market Cyberware", "Stolen Source Code", "Weaponized AI"],
                "hazards": ["ICE-Attack", "Neural Burnout", "Toxic Rain", "Rogue Drones", "Corporate Hit-squads"],
                "material": ["Silicon", "Synthetic-Flesh", "Graphene", "Lithium", "Neon-Gas"],
                "outcome": ["Corp successfully covered it up", "Thousands of nodes were fried", "The perpetrators were zeroed", "Led to a total market crash"],
                "secret_truth": ["The AI orchestrated it to escape", "The CEO shorted his own stock before the crash", "It was a false flag operation by a rival corp"]
            },
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
            document_types=["Cargo Manifest", "Comms Intercept", "Life Support Log", "Contraband Ledger", "Colony Directive", "Incident Report", "Refinery Output", "Mutiny Declaration", "Captain's Final Log", "Alien Artifact Analysis"],
            document_structures=[
                "Format as a claustrophobic, oxygen-deprived audio log transcript (e.g. [Heavy Breathing], [Static]). Tone should be paranoid and desperate.",
                "Format as a cold, calculating station AI output, analyzing crew behavior with chilling apathy.",
                "Format as a smuggled handwritten note passed between miners, planning a violent union strike.",
                "Format as an official military-style incident report, but filled with impossible or horrific details.",
                "Format as a dry cargo manifest that slowly reveals something terrifying hidden in the freight."
            ],
            naming_banks={
                "name_person": ["Ripley", "Dallas", "Hicks", "Vasquez", "Bishop", "Gorman", "Hudson", "Burke", "Apone", "Frost", "Dietrich", "Spunkmeyer"],
                "name_facility": ["Aegis-7", "Hadley's Hope", "Sevastopol Station", "Tartarus Mine", "Sector 4", "Cryo-Bay B", "Airlock 12"],
                "name_crisis": ["The Oxygen Riots", "The Xenomorph Incursion", "The Tartarus Mutiny", "Reactor Meltdown Alpha", "The Deep Space Madness"],
                "region": ["Asteroid Belt", "Outer Rim", "Deep Space", "Orbiting Gas Giant", "The Dark Zone", "Mining Sector 4"],
                "role": ["Miner", "Captain", "Engineer", "Marine", "Medic", "Pilot", "Navigator", "Corporate Liaison"],
                "specialty": ["Heavy Machinery", "Astrogation", "Xeno-biology", "Demolitions", "Zero-G Combat", "Medical triage"],
                "clearance": ["Level 1", "Level 4", "Captain", "Weyland-Yutani Only", "Classified", "Civilian"],
                "secret": ["Infected by a parasite", "Sabotaging the life support", "Smuggling alien eggs", "Spying for a rival corp"],
                "contraband": ["Alien Artifacts", "Unregistered Weapons", "Stolen Oxygen Tanks", "Narcotics"],
                "hazards": ["Hull Breach", "Radiation", "Alien Organism", "Oxygen Depletion", "Extreme Cold"],
                "material": ["Promethium", "Tritium", "Xenomorph Resin", "Platinum", "Ice"],
                "outcome": ["The entire sector was vented into space", "The mutineers were executed", "The station was abandoned", "The corp covered it up as a meteor strike"],
                "secret_truth": ["The corp ordered the release of the organism", "The captain deliberately crashed the ship", "The distress signal was a trap"]
            },
            corpus_distribution=CorpusDistribution(
                image_injection_ratio=0.10,
                format_ratios={".pdf": 0.40, ".png": 0.20, ".docx": 0.20, ".txt": 0.20}
            ),
            start_year=2310,
            end_year=2350
        )
