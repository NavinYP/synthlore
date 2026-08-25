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

    def _build_system_prompt(self, doc_type: str, world_prompt: str = None) -> str:
        prompt = (
            f"You are an automated archivist in a {self.config.setting_name} universe. "
            "Your job is to generate a highly immersive, aesthetically appropriate in-world document.\n"
        )
        
        if world_prompt:
            prompt += f"\n### EXTENDED WORLD-BUILDING CONTEXT ###\n{world_prompt}\n\n"
            
        # Add dynamic structural rules based on the document type
        doc_lower = doc_type.lower()
        structure_rules = ""
        if any(k in doc_lower for k in ["transcript", "intercept", "interrogation"]):
            structure_rules = "STRUCTURE: Format strictly as a raw dialogue transcript with SPEAKER labels and [BRACKETED] audio descriptions (e.g., [Static], [Sighs])."
        elif any(k in doc_lower for k in ["diary", "journal", "cache", "scrawl"]):
            structure_rules = "STRUCTURE: Format as a fragmented, deeply personal, and paranoid first-person narrative. Use erratic pacing."
        elif any(k in doc_lower for k in ["pamphlet", "manifesto", "prophecy", "liturgy"]):
            structure_rules = "STRUCTURE: Format as passionate, zealous, or heretical prose. Use rhetorical questions, capitalization for emphasis, and grand allegories."
        elif any(k in doc_lower for k in ["missive", "letter", "grievance"]):
            structure_rules = "STRUCTURE: Format as formal correspondence with a Salutation, Body, and Sign-off. Tone should be politically tense or aggressively bureaucratic."
        elif any(k in doc_lower for k in ["ledger", "manifest", "schedule", "audit"]):
            structure_rules = "STRUCTURE: Format primarily as a dry, clinical table or bulleted list of items, interspersed with terse, cold annotations."
        else:
            structure_rules = "STRUCTURE: Format as a standard corporate or military report with clear headings, status indicators, and executive summaries."

        prompt += (
            f"You must strictly format this text as a: {doc_type}. {structure_rules}\n"
            "The tone, structure, and prose should perfectly match this medium. "
            "CRITICAL RULES:\n"
            "1. NO REAL WORLD ENTITIES. Do not mention Earth, modern companies, real historical events, etc.\n"
            "2. STRICT FACTUAL ADHERENCE. The relationships and entities provided in the context are ABSOLUTE GROUND TRUTH. "
            "You may invent prose, sensory details, and narrative flavor, but you MUST NOT contradict the provided edges, "
            "and you MUST NOT invent new named entities (guilds/reactors) that are not in the context.\n"
            "3. FORMAT: Output the document as Markdown. Make it look like an authentic artifact."
        )
        return prompt

    async def compile_document(self, graph: nx.DiGraph, node_id: str, doc_type: str = "Technical Manual", world_prompt: str = None) -> str:
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
            system_prompt=self._build_system_prompt(doc_type=doc_type, world_prompt=world_prompt)
        )
        
        return document_text
