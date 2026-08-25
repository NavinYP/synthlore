import pytest
import networkx as nx
from src.graph.config import WorldConfig, EdgeType
from src.graph.generator import KnowledgeGraphGenerator

@pytest.fixture
def test_config():
    return WorldConfig(
        setting_name="Test World",
        entity_types=["A", "B"],
        edge_types=[
            EdgeType(name="CONNECTS_TO", source_type="A", target_type="B")
        ],
        start_year=2000,
        end_year=2020
    )

def test_config_initialization(test_config):
    assert test_config.setting_name == "Test World"
    assert "A" in test_config.entity_types

def test_default_arcane_config():
    config = WorldConfig.default_arcane_industrial()
    assert config.setting_name == "Arcane Industrial"
    assert len(config.entity_types) >= 5

def test_graph_generation(test_config):
    generator = KnowledgeGraphGenerator(test_config)
    graph = generator.generate(num_nodes=50)
    
    assert isinstance(graph, nx.DiGraph)
    assert graph.number_of_nodes() == 50
    
    # Check that all nodes have valid types and temporal data
    for node_id, data in graph.nodes(data=True):
        assert data['type'] in ["A", "B"]
        assert 2000 <= data['established'] <= 2020
        assert "name" in data
        assert "active" in data

    # Check that all edges follow the allowed rules
    for u, v, data in graph.edges(data=True):
        source_type = graph.nodes[u]['type']
        target_type = graph.nodes[v]['type']
        
        assert source_type == "A"
        assert target_type == "B"
        assert data['relation'] == "CONNECTS_TO"
        assert "timestamp" in data
        assert data['timestamp'] >= graph.nodes[u]['established']

def test_graph_stats():
    config = WorldConfig.default_arcane_industrial()
    generator = KnowledgeGraphGenerator(config)
    generator.generate(num_nodes=50)
    
    stats = generator.get_graph_stats()
    assert stats["num_nodes"] == 50
    assert stats["setting"] == "Arcane Industrial"
    assert stats["is_directed"] is True
