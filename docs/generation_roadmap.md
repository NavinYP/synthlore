# 🗺️ Generation Roadmap

This document outlines the phased approach to generating the synthetic multi-modal corporate corpus.

## The "Why" Behind the Pipeline
Traditional synthetic data generation relies heavily on the LLM to invent facts on the fly. This leads to internal contradictions, hallucinated edge-cases, and an inability to accurately score RAG systems because the "ground truth" is malleable.

By inverting the process—generating a mathematical graph *first*, and using the LLM strictly as a translator—we guarantee that every document, chart, and ledger perfectly aligns with a verifiable reality.

## Phase 1: Foundation & Graph Engine
**Goal:** Generate the mathematical "Ground Truth" of the world.
**Tasks:**
- Define schema: Node Types (Person, Facility, Gear) and Edge Types (WORKS_AT, MAINTAINS, REQUIRES).
- Write procedural graph generator `src/graph/generator.py` using `networkx`.
- Ensure high interconnectivity (small-world properties) for complex multi-hop queries.

## Phase 2: Text Compilation (COMPLETED)
**Goal:** Translate local graph neighborhoods into coherent, stylized documents.
**Tasks:**
- Select N "Focal Nodes".
- Extract 1-hop and 2-hop subgraphs around each focal node.
- Write `src/generation/document_compiler.py` to prompt `gpt-5.6-luna` to write a stylized document (e.g. Memo, Diary, Ledger) strictly constrained by the subgraph context.

## ✅ Phase 3: Visual Generation & Layouts (COMPLETED)
**Goal:** Convert textual documents into visually "noisy" artifacts to test OCR, Vision Models, and Multimodal reasoning.
**Tasks:**
- [x] Create `src/generation/visual_renderer.py` using `Pillow`.
- [x] Integrate `gpt-image-2` to dynamically generate blueprint assets based on Graph entities.
- [x] Programmatically composite the visual assets into the document layout.
- [x] Support multi-format exports (`.pdf`, `.png`, `.docx`, `.txt`).
- [x] Dynamically expand document canvas height to ensure embedded images are never truncated.
- [x] Implement asynchronous parallelization using `asyncio.gather` and Semaphores to bypass standard sequential API latency.
- [x] Add execution timing metrics, `tqdm` progress bars, and file-based logging (`generation.log`).

### ⏱️ Performance Metrics & Final Run ETA
Based on a controlled 10-document sample (`output/sample_corpus_20260826_011256`) using the optimized 10% distribution configuration:
- **`gpt-5.6-luna` (Text):** ~8.1s per document
- **`gpt-image-2` (Assets):** ~90.7s per image
- **Rendering (.pdf/.png/.docx):** ~0.07s per document

**ETA for Final 2,000 Document Corpus (Sequential):**
- 2,000 Text docs = ~4.5 hours *(Note: We will migrate this to Azure Global Batch API to drastically reduce this).*
- 200 Visual Assets (10%) = ~5.0 hours
- **Total Estimated Run Time:** ~9.5 hours (Down from 20.5 hours by adjusting distribution logic).

## ✅ Phase 4: Benchmark Extraction & Q&A Generation (COMPLETED)
**Goal:** Generate the rigorous evaluation questions the final RAG agents will face.
**Tasks:**
- [x] Implemented `o3` evaluation configs mapping to SLIIT Codefest tracks (Multimodal, Multi-hop, Agentic RAG).
- [x] Enforced strict validation (`nx.has_path` and `nx.shortest_path_length == 2`) to eliminate unintended direct edge leakage (A -> C) ensuring true Multi-hop challenges.
- [x] Generated `benchmark_qa.json` paired tightly with each sample set run.

## ✅ Phase 5: Final Polish, Hardening, & Delivery (COMPLETED)
**Goal:** Finalize the project for robust generation and open-source release.
**Tasks:**
- [x] **Agentic Contradictions**: Implemented `inject_contradictions()` to create verifiable "Unreliable Narrator" documents, forcing dynamic conflict resolution for Track 1C.
- [x] **Multimodal Data Isolation**: Dynamically injected precise quantitative facts (capacity, throughput) directly into `gpt-image-2` charts. This ensures numerical facts exist *only* in pixels, not text.
- [x] **Clean Output Architecture**: Separated execution logic so all raw intermediate files stay in the root run directory, while the final, polished artifacts (PDFs, DOCX, TXT, and Standalone PNGs) are strictly outputted to a `processed/` directory. 
- [x] **Standalone Visual Assets**: Extracted `gpt-image-2` generations as standalone `.png` files (e.g. `_Blueprint.png`, `_Chart.png`) within the processed folder, apart from being embedded inside DOCX/PDFs.
- [x] **Custom World-Building**: Supported a `--world_prompt` CLI flag, allowing specific aesthetic and narrative direction (e.g., Arcane, Cyberpunk, Deep Space) seamlessly embedded into the lore prompt.

## ✅ Phase 6: Franchise Ecosystem Pivot (COMPLETED)
**Goal:** Shift the pipeline output from short, disconnected "bureaucratic memos" into massive, sprawling Franchise Ecosystems (Novels, Fandom Wikis, RPG Codexes) to rival *Warhammer* or *ASOIAF*.
**Tasks:**
- [x] **Core Cast Gravity Well**: Overhauled `KnowledgeGraphGenerator` so that a select few entities form a "Core Cast". Edges preferentially cluster around these protagonists, strongholds, and epic crises (e.g., *The Fall of Vaeloria*), ensuring the dataset is deeply interwoven for complex RAG tasks.
- [x] **Long-Form Narrative Generation**: Rewrote the `DocumentCompiler` prompt to explicitly forbid short summaries. The LLM now generates 1000+ word *Novel Chapters*, *Wiki Articles* (with Infoboxes), and *In-Universe Histories*.
- [x] **Dynamic Franchise Visuals**: Replaced the static "blueprint/chart" logic with dynamic visual franchise assets. The pipeline now reads the graph entity type and leverages `gpt-image-2` to generate gorgeous Character Portraits, Landscape Maps, Faction Heraldry, and Relic illustrations.
- [x] **Theme-Agnostic Abstraction**: Decoupled all hardcoded naming banks and structures from the generators and moved them strictly into `WorldConfig`. The entire ecosystem can dynamically shift between Cyberpunk, Grim Fantasy, or Deep Space effortlessly.

**All systems are now operational. The pipeline successfully executes highly-concurrent batches of complex, graph-backed synthetic corpora in under 2 minutes for small scale tests.**
