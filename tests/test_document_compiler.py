import pytest
import networkx as nx
from src.graph.config import WorldConfig
from src.generation.document_compiler import DocumentCompiler

class DummyLLMClient:
    async def generate_lore(self, prompt: str, system_prompt: str, temperature: float) -> str:
        return "# Dummy Document\n\nGenerated text based on facts."

@pytest.mark.asyncio
async def test_extract_subgraph_context():
    config = WorldConfig.default_arcane_industrial()
    compiler = DocumentCompiler(llm_client=DummyLLMClient(), config=config)
    
    # Create mock graph
    G = nx.DiGraph()
    G.add_node("n1", name="Guild-Alpha", type="Guild")
    G.add_node("n2", name="Reactor-X", type="Aether-Reactor")
    G.add_edge("n1", "n2", relation="MANUFACTURES", timestamp=1850)
    
    context = compiler.extract_subgraph_context(G, "n1")
    
    assert "FOCAL ENTITY:" in context
    assert "Guild-Alpha" in context
    assert "[1850] Guild-Alpha MANUFACTURES Reactor-X" in context

@pytest.mark.asyncio
async def test_compile_document():
    config = WorldConfig.default_arcane_industrial()
    compiler = DocumentCompiler(llm_client=DummyLLMClient(), config=config)
    
    G = nx.DiGraph()
    G.add_node("n1", name="Guild-Alpha", type="Guild")
    
    doc = await compiler.compile_document(G, "n1")
    assert "Dummy Document" in doc
