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
- Create `src/generation/visual_renderer.py` using `Pillow`.
- Integrate `gpt-image-2` to dynamically generate blueprint assets based on Graph entities.
- Programmatically composite the visual assets into the document layout.
- Support multi-format exports (`.pdf`, `.png`, `.docx`, `.txt`).
- Dynamically expand document canvas height to ensure embedded images are never truncated.
- Add execution timing metrics to estimate final run duration.

### ⏱️ Performance Metrics & Final Run ETA
Based on a controlled 10-document sample (`output/sample_corpus_20260826_011256`) using the optimized 10% distribution configuration:
- **`gpt-5.6-luna` (Text):** ~8.1s per document
- **`gpt-image-2` (Assets):** ~90.7s per image
- **Rendering (.pdf/.png/.docx):** ~0.07s per document

**ETA for Final 2,000 Document Corpus (Sequential):**
- 2,000 Text docs = ~4.5 hours *(Note: We will migrate this to Azure Global Batch API to drastically reduce this).*
- 200 Visual Assets (10%) = ~5.0 hours
- **Total Estimated Run Time:** ~9.5 hours (Down from 20.5 hours by adjusting distribution logic).

## Phase 4: Benchmark Extraction & Q&A Generation
**Goal:** Generate the rigorous evaluation questions the final RAG agents will face.
**Tasks:**
- Prompt `o3` to read the entire Graph structure and synthesize complex multi-hop questions (e.g. "If the Aether-Reactor at Site B fails, which Smuggler's diary reveals the backup supply route?").
- Ensure questions are answerable *only* by reading across multiple modalities (e.g. identifying a part from a blueprint in a PDF, and cross-referencing a name from a noisy PNG ledger).

## Phase 5: Polish & Documentation
**Goal:** Finalize the project for open-source / Medium article release.
