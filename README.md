# SyntheticLore-Bench

SyntheticLore-Bench is a Python-based synthetic data generator designed to create a 2,000-page fictional document corpus and an accompanying Q&A ground-truth benchmark. This project is purpose-built to evaluate advanced Retrieval-Augmented Generation (RAG) systems across Multimodal, Multi-hop, and Agentic tracks.

## Core Philosophy

To guarantee **zero data leakage** and prevent LLMs from hallucinating internal contradictions, SyntheticLore-Bench adopts a **Graph-First Architecture**. 
All entities and relationships are modeled as a Directed Graph (using NetworkX) *before* any text generation occurs. The LLM acts purely as a translator, turning exact k-hop subgraph structures into narrative text.

## Documentation

- [Architecture Decision Record (ADR)](docs/architecture_decision_record.md): Explains the technical choices, dynamic aesthetic configurations, and Multimodal integrations.
- [Generation Roadmap](docs/generation_roadmap.md): Outlines the 5-phase test-driven execution strategy.
- [Azure OpenAI Setup Guide](docs/azure_setup_guide.md): 2026 guidelines for configuring Azure AI Foundry to power the generation pipeline.

## Quick Start (Phase 1)

1. **Clone the repository:**
   ```bash
   git clone git@github.com:NavinYP/synthlore.git
   cd synthlore
   ```

2. **Set up a virtual environment and install dependencies:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the Graph Engine Tests:**
   ```bash
   PYTHONPATH=$(pwd) pytest tests/
   ```

## License
This project is licensed under the [MIT License](LICENSE).
