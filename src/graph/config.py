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
    core_counts: Dict[str, int] = field(default_factory=dict)

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

    @classmethod
    def default_grim_fantasy(cls):
        return cls(
            setting_name="The Ashen Empire of Vaeloria",
            tone="Grimdark fantasy, steeped in blood-magic, theological zealotry, and brutal feudal politics. Noble houses and militant religious orders vie for control over ancient, dying Ley-Engines. Deep lore, paranoid tone, betrayal, and hidden conspiracies.",
            factions=["Order of the Ashen Dawn", "House Morvain", "The Iron-Ring Cartel", "The Silent Choir", "The Bleeding Crown"],
            node_types=[
                NodeType(name="Person", properties=["name", "role", "faction", "secret"]),
                NodeType(name="Ley-Engine", properties=["name", "capacity", "status", "location"]),
                NodeType(name="Stronghold", properties=["name", "region", "throughput", "manager"]),
                NodeType(name="Order", properties=["name", "specialty", "influence"]),
                NodeType(name="Inquisitor", properties=["name", "clearance_level", "assigned_hub"]),
                NodeType(name="Blood-Forge", properties=["name", "output_material", "hazards"]),
                NodeType(name="Historical Crisis", properties=["name", "casualty_rate", "outcome", "secret_truth"])
            ],
            edge_types=[
                EdgeType(name="COMMANDS", source_type="Person", target_type="Stronghold", description="Leadership"),
                EdgeType(name="BINDS", source_type="Person", target_type="Ley-Engine", description="Magical maintenance"),
                EdgeType(name="POWERED_BY", source_type="Stronghold", target_type="Ley-Engine", description="Energy dependency"),
                EdgeType(name="SWORN_TO", source_type="Person", target_type="Order", description="Fealty"),
                EdgeType(name="TITHES_TO", source_type="Blood-Forge", target_type="Stronghold", description="Material flow"),
                EdgeType(name="PURGES", source_type="Inquisitor", target_type="Stronghold", description="Religious Inspection"),
                EdgeType(name="ORCHESTRATED", source_type="Person", target_type="Historical Crisis", description="Secretly caused the event"),
                EdgeType(name="DEVASTATED_BY", source_type="Stronghold", target_type="Historical Crisis", description="Suffered during the event"),
                EdgeType(name="PROFIT_FROM", source_type="Order", target_type="Historical Crisis", description="Capitalized on the tragedy")
            ],
            document_types=["Fandom Wiki Article", "Novel Chapter", "Lore Codex Entry", "In-Universe Historical Tome", "Noble House Lineage"],
            document_structures=[
                "Format as a comprehensive Fandom Wiki Article. Include a structured 'Infobox' at the top with key stats, followed by sections for 'History', 'Relationships', and 'Trivia'. Write at least 800 words.",
                "Format as an epic, grimdark Fantasy Novel Chapter. Focus heavily on prose, atmosphere, internal monologue, and dialogue. The scene must vividly explore the focal entity and its connections. Write at least 800 words.",
                "Format as an exhaustive Lore Codex Entry from an official RPG or tabletop game rulebook. Include detailed historical lore, strategic importance, and dark secrets. Write at least 800 words.",
                "Format as an In-Universe Historical Tome. Write with the subjective, highly biased voice of an Imperial Scholar or Inquisitor recounting ancient betrayals. Write at least 800 words."
            ],
            naming_banks={
                "name_person": ["Malakor", "Vaelia", "Draven", "Elysia", "Gorath", "Lucius", "Seraph", "Vortigern", "Nyra", "Caius", "Isolde", "Ravenscroft", "Grimshaw"],
                "name_facility": ["Sunken Cathedral", "Obsidian Keep", "The Harrow-Vault", "Crimson Spire", "Iron-Hold", "The Whispering Tower", "Golgotha Fortress"],
                "name_crisis": ["The Night of Blackened Knives", "The Schism of the Ashen Dawn", "The Crimson Plague", "The Fall of Vaeloria", "The Heresy of House Morvain"],
                "region": ["The Ash Wastes", "The Weeping Marshes", "The High Spires", "The Sunless Depths", "The Pale Coast", "The Blood-Moor"],
                "role": ["High Inquisitor", "Blood-Mage", "Oathbreaker", "Sellsword", "Zealot", "Arch-Prelate", "Spymaster", "Executioner"],
                "specialty": ["Necromancy", "Demonology", "Political Assassination", "Ley-Line Tapping", "Smuggling", "Heretical Texts"],
                "clearance": ["Grand Master", "Inner Circle", "Initiate", "Excommunicated", "Anointed", "Black-Marked"],
                "secret": ["Harboring a demon", "Secretly a blood-mage", "Falsified their noble lineage", "Plotted the Arch-Prelate's murder", "Stealing Ley-energy"],
                "contraband": ["Crimson Lotus", "Wraith-bone", "Purified Ley-blood", "Cursed Silver", "Heretical Texts", "Demon-Ash"],
                "hazards": ["Demonic Incursion", "Ley-Radiation", "Blood-Plague", "Zealot Uprising", "Structural Collapse"],
                "material": ["Wraith-bone", "Cursed Silver", "Ley-Crystals", "Abyssal Iron", "Purified Blood"],
                "outcome": ["The stronghold was purged with holy fire", "The noble house was entirely assassinated", "The truth was buried by the Inquisition", "The demonic entity escaped"],
                "secret_truth": ["The Inquisition started the plague", "The Arch-Prelate is possessed", "House Morvain was framed", "The Ley-Engines are fueled by human souls"]
            },
            corpus_distribution=CorpusDistribution(
                image_injection_ratio=0.10,
                format_ratios={".pdf": 0.40, ".png": 0.20, ".docx": 0.20, ".txt": 0.20}
            ),
            start_year=800,
            end_year=1024
        )


    @classmethod
    def default_franchise_ecosystem(cls):
        return cls(
            setting_name="Warhammer 40k / Deep Fantasy Franchise",
            tone="Dark, meticulously crafted fictional universe. High interconnectivity between major characters, core locations, artifacts, and historical conflicts.",
            factions=["The Ashen Vanguard", "House Morvain", "The Iron-Ring Cartel", "The Silent Choir", "The Bleeding Crown"],
            node_types=[
                NodeType(name="Major Character", properties=["name", "role", "faction", "secret"]),
                NodeType(name="Key Artifact", properties=["name", "capacity", "status", "location"]),
                NodeType(name="Core Location", properties=["name", "region", "throughput", "manager"]),
                NodeType(name="Historical Conflict", properties=["name", "casualty_rate", "outcome", "secret_truth"])
            ],
            edge_types=[
                EdgeType(name="COMMANDS", source_type="Major Character", target_type="Core Location", description="Leadership"),
                EdgeType(name="WIELDS", source_type="Major Character", target_type="Key Artifact", description="Magical maintenance"),
                EdgeType(name="HOUSED_IN", source_type="Key Artifact", target_type="Core Location", description="Energy dependency"),
                EdgeType(name="FOUGHT_IN", source_type="Major Character", target_type="Historical Conflict", description="Participation in war"),
                EdgeType(name="DESTROYED_IN", source_type="Core Location", target_type="Historical Conflict", description="Suffered during the event"),
                EdgeType(name="USED_IN", source_type="Key Artifact", target_type="Historical Conflict", description="Artifact was utilized in this battle"),
                EdgeType(name="ALLIED_WITH", source_type="Major Character", target_type="Major Character", description="Alliance"),
                EdgeType(name="ENEMIES_WITH", source_type="Major Character", target_type="Major Character", description="Rivalry")
            ],
            document_types=["The Chronicles", "The Lore Wiki", "The Technical Codex"],
            document_structures=[
                "Format as 'The Chronicles' (Narrative): A long-form chapter (approx. 10-20 pages equivalent in depth) describing historical conflicts and character journeys in flowing prose.",
                "Format as 'The Lore Wiki' (Structured): A wiki-style page focusing on a single entity with structured headers, summaries, and cross-references.",
                "Format as 'The Technical Codex' (Data-Heavy): A Data Book or Manual that reads like technical specifications, rulebooks, or logistics ledgers."
            ],
            naming_banks={
                "name_person": ["Malakor", "Vaelia", "Draven", "Elysia", "Gorath", "Lucius", "Seraph", "Vortigern", "Nyra", "Caius", "Isolde", "Ravenscroft", "Grimshaw"],
                "name_facility": ["Sunken Cathedral", "Obsidian Keep", "The Harrow-Vault", "Crimson Spire", "Iron-Hold", "The Whispering Tower", "Golgotha Fortress"],
                "name_crisis": ["The Night of Blackened Knives", "The Schism of the Ashen Dawn", "The Crimson Plague", "The Fall of Vaeloria", "The Heresy of House Morvain"],
                "region": ["The Ash Wastes", "The Weeping Marshes", "The High Spires", "The Sunless Depths", "The Pale Coast", "The Blood-Moor"],
                "role": ["High Inquisitor", "Blood-Mage", "Oathbreaker", "Sellsword", "Zealot", "Arch-Prelate", "Spymaster", "Executioner"],
                "specialty": ["Necromancy", "Demonology", "Political Assassination", "Ley-Line Tapping", "Smuggling", "Heretical Texts"],
                "clearance": ["Grand Master", "Inner Circle", "Initiate", "Excommunicated", "Anointed", "Black-Marked"],
                "secret": ["Harboring a demon", "Secretly a blood-mage", "Falsified their noble lineage", "Plotted the Arch-Prelate's murder", "Stealing Ley-energy"],
                "contraband": ["Crimson Lotus", "Wraith-bone", "Purified Ley-blood", "Cursed Silver", "Heretical Texts", "Demon-Ash"],
                "hazards": ["Demonic Incursion", "Ley-Radiation", "Blood-Plague", "Zealot Uprising", "Structural Collapse"],
                "material": ["Wraith-bone", "Cursed Silver", "Ley-Crystals", "Abyssal Iron", "Purified Blood"],
                "outcome": ["The stronghold was purged with holy fire", "The noble house was entirely assassinated", "The truth was buried by the Inquisition", "The demonic entity escaped"],
                "secret_truth": ["The Inquisition started the plague", "The Arch-Prelate is possessed", "House Morvain was framed", "The Ley-Engines are fueled by human souls"]
            },
            corpus_distribution=CorpusDistribution(
                image_injection_ratio=0.30,
                format_ratios={".pdf": 0.40, ".png": 0.20, ".docx": 0.20, ".txt": 0.20}
            ),
            start_year=800,
            end_year=1024,
            core_counts={
                "Major Character": 15,
                "Core Location": 10,
                "Historical Conflict": 5,
                "Key Artifact": 20
            }
        )
