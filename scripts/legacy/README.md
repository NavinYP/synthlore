# Legacy Pipeline Scripts (Phases 2–6)

These scripts belong to the earlier **Ego-Graph (Document-per-Node)** iterations of SyntheticLore-Bench (Phases 2 through 6). They are preserved here for architectural reference and comparison against the Phase 7 **Fact-Placement Competition Pipeline** (`scripts/generate_competition_corpus.py`).

## Why We Evolved Beyond Ego-Graph Dumps
In Phases 2–6 (`generate_sample_corpus.py`, `generate_franchise_volumes.py`), each document was compiled by extracting the $k$-hop ego-graph around a focal entity (`src/generation/document_compiler.py`). While effective for generating rich standalone lore, ego-graph dumps allow a single retrieved bridge document to contain both edges of a 2-hop chain—inadvertently collapsing multi-hop RAG questions into single-hop lookups.

For the benchmark-valid competition pipeline that enforces strict multi-hop isolation, programmatic visual plates, and authority-tiered epistemic conflicts, see [`../generate_competition_corpus.py`](../generate_competition_corpus.py).
