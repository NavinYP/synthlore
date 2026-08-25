import networkx as nx
from typing import List, Dict, Any
from src.graph.config import WorldConfig
from src.generation.llm_client import UnifiedAIClient

class DocumentCompiler:
    def __init__(self, llm_client: UnifiedAIClient, config: WorldConfig):
        self.client = llm_client
        self.config = config

    def extract_subgraph_context(self, graph: nx.DiGraph, center_node: str, radius: int = 1) -> str:
        """
        Extracts a k-hop neighborhood around the center node and formats it into a factual text context.
        """
        # Create an ego graph (k-hop neighborhood)
        subgraph = nx.ego_graph(graph, center_node, radius=radius)
        
        context_lines = []
        context_lines.append(f"FOCAL ENTITY:")
        
        node_data = subgraph.nodes[center_node]
        context_lines.append(f"- ID: {center_node}")
        for k, v in node_data.items():
            if k == "contradictions":
                context_lines.append("\n*** CONTRADICTION DETECTED ***")
                context_lines.append(f"AGENTIC INSTRUCTION: The following is FALSE but you must weave it into the document as a rumor, error, or unverified claim by an unreliable narrator: {v['narrative']}")
                context_lines.append("******************************\n")
            else:
                context_lines.append(f"- {k.capitalize()}: {v}")
            
        context_lines.append("\nRELATIONSHIPS:")
        for u, v, data in subgraph.edges(data=True):
            source_name = subgraph.nodes[u].get('name', u)
            target_name = subgraph.nodes[v].get('name', v)
            rel_type = data.get('relation', 'RELATES_TO')
            timestamp = data.get('timestamp', 'Unknown Era')
            
            context_lines.append(f"- [{timestamp}] {source_name} {rel_type} {target_name}")
            
        return "\n".join(context_lines)

    def _build_system_prompt(self, doc_type: str, world_prompt: str = None, structure_rule: str = None) -> str:
        prompt = (
            f"You are a masterful world-builder and archivist in a {self.config.setting_name} universe. "
            "Your job is to generate highly immersive, expansive, and deeply detailed in-world literature. "
            "DO NOT write short, simple summaries. Write like a bestselling adult dark fantasy author or a dedicated grimdark franchise lore-master. The tone MUST be highly sophisticated, deeply mature, and unflinchingly brutal. Absolutely NO childish language, whimsical tones, or simplistic vocabulary. Use complex sentence structures, archaic or clinical terminology where appropriate, and focus on the grim, serious reality of this universe.\n"
        )
        if world_prompt:
            prompt += f"\n### EXTENDED WORLD-BUILDING CONTEXT ###\n{world_prompt}\n\n"
        if doc_type == "The Chronicles":
            structure_rule = (
                "Format as 'The Chronicles' (Narrative). Write a long-form chapter (approx 10-20 pages equivalent in depth, minimum 1000 words). "
                "Describe historical conflicts and character journeys in flowing, dramatic prose. "
                "Focus on subjective perspectives, internal monologues, and rich sensory details."
            )
        elif doc_type == "The Lore Wiki":
            structure_rule = (
                "Format as 'The Lore Wiki' (Structured). Write a wiki-style page focusing on a single entity. "
                "Include a structured 'Infobox' at the top with key stats using Markdown tables. "
                "Use standard Markdown headers (e.g., ## History, ## Associated Artifacts, ## Known Affiliations). "
                "Crucially, create pseudo-hyperlinks for cross-references like [Entity Name] when mentioning other entities."
            )
        elif doc_type == "The Technical Codex":
            structure_rule = (
                "Format as 'The Technical Codex' (Data-Heavy). Write a Data Book, Manual, or Logistics Ledger. "
                "Focus on dry, clinical, and data-heavy outputs. Heavily utilize tables, bulleted procedures, "
                "aether-pressure readings, garrison counts, and structured status reports. It must read like an engineering rulebook."
            )
        elif not structure_rule:
            structure_rule = "Format as a standard corporate or military report with clear headings, status indicators, and executive summaries."
        prompt += (
            f"You must strictly format this text as a: {doc_type}. \n"
            f"STRUCTURE OVERRIDE: {structure_rule}\n"
            "The tone, structure, and prose should perfectly match this medium. "
            "CRITICAL RULES:\n"
            "1. LENGTH & DEPTH: This must be a long-form, comprehensive document. Expand on the lore.\n"
            "2. NO REAL WORLD ENTITIES. Do not mention Earth, modern companies, real historical events, etc.\n"
            "3. STRICT FACTUAL ADHERENCE. The relationships and entities provided in the context are ABSOLUTE GROUND TRUTH. "
            "You MUST NOT contradict the provided edges, and you MUST NOT invent new named entities not in the context.\n"
            "4. FORMAT: Output the document as Markdown."
        )
        return prompt
    async def compile_document(self, graph: nx.DiGraph, node_id: str, doc_type: str = "Technical Manual", world_prompt: str = None, structure_rule: str = None) -> str:
        """
        Extracts context for a node and calls the LLM to generate the document.
        """
        context = self.extract_subgraph_context(graph, node_id, radius=1)
        
        prompt = (
            "Please generate an in-world document focusing on the following focal entity and its relationships.\n\n"
            "### GROUND TRUTH CONTEXT\n"
            f"{context}\n\n"
            "### INSTRUCTIONS\n"
            "Write the document from the perspective of an entity or person interacting with the focal entity. "
            "Weave the relationships naturally into the narrative or technical log."
        )
        
        # Call the bulk lore generation endpoint (e.g., gpt-5.6-luna)
        document_text = await self.client.generate_lore(
            prompt=prompt,
            system_prompt=self._build_system_prompt(doc_type=doc_type, world_prompt=world_prompt, structure_rule=structure_rule)
        )
        
        return document_text
