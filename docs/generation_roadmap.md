# Generation Roadmap: SyntheticLore-Bench

This roadmap outlines the phased execution strategy for building the SyntheticLore-Bench corpus. Our philosophy is rooted in **Test-Driven Generation** and **Strict Ground-Truth Adherence**.

## The "Why" Behind the Pipeline
Traditional synthetic data generation relies heavily on the LLM to invent facts on the fly. This leads to internal contradictions, hallucinated edge-cases, and an inability to accurately score RAG systems because the "ground truth" is malleable.

By inverting the process—generating a mathematical graph *first*, and using the LLM strictly as a translator—we guarantee that every document, chart, and ledger perfectly aligns with a verifiable reality.

## Phase 1: Foundation & Graph Engine
*   **Objective:** Build the mathematical foundation of the fictional universe.
*   **Key Deliverable:** `WorldConfig` schema and the `KnowledgeGraphGenerator`.
*   **Status:** **Completed**.

## Phase 2: Text Compilation
*   **Objective:** Transform graph nodes and edges into narrative markdown.
*   **Strategy:** Extract k-hop subgraphs (a localized cluster of nodes/edges) and prompt an Azure OpenAI model to write a document based strictly on that cluster.
*   **Status:** Upcoming.

## Phase 3: Asset Weaving
*   **Objective:** Introduce Multimodal complexity for RAG evaluation.
*   **Strategy:** Intercept numerical/tabular nodes (e.g., Aether-Reactor output logs) and render them programmatically using `matplotlib` (charts) and `Pillow` (scanned ledgers). Inject these as image links into the markdown.
*   **Status:** Upcoming.

## Phase 4: Benchmark Extraction
*   **Objective:** Create the actual Q&A evaluation dataset.
*   **Strategy:** Traverse the NetworkX graph to programmatically generate questions. For example, a 3-hop question: *"Which Dispatch Hub regulates the reactor that is supplied by Foundry X?"* The graph provides the exact, undeniable answer.
*   **Status:** Upcoming.

## Phase 5: Refinement & Scale
*   **Objective:** Scale up to the 2,000-page target and open-source the benchmark.
*   **Strategy:** Utilize async LLM batching via Azure AI Foundry, finalize documentation, and prepare the Medium article publication.
*   **Status:** Upcoming.
