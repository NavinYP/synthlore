# Architecture Decision Record (ADR): SyntheticLore-Bench

## 1. Title
**Graph-First RAG Evaluation Corpus Generation with Dynamic Aesthetics**

## 2. Status
**Accepted**

## 3. Context
We need to generate a 2,000-page synthetic corpus and corresponding ground-truth Q&A benchmark to evaluate advanced Retrieval-Augmented Generation (RAG) systems across Multimodal, Multi-hop, and Agentic tracks. To prevent LLMs from relying on pre-trained knowledge (data leakage), the dataset must be entirely fictional.

## 4. Decisions

### 4.1 Graph-First Architecture (NetworkX)
*   **Decision:** All entities and relationships are modeled as a Directed Graph (`nx.DiGraph`) *before* any text generation occurs.
*   **Rationale:** Ensures absolute logical consistency and a rigorous ground-truth for complex multi-hop queries. The LLM does not hallucinate facts; it only translates subgraphs into natural language.

### 4.2 Dynamic Aesthetic Configuration (WorldConfig)
*   **Decision:** The thematic setting (e.g., "Arcane Industrial") is decoupled from the pipeline code using a Pydantic `WorldConfig` model.
*   **Rationale:** Allows the generator to scale or pivot to new settings (e.g., "Cyberpunk", "Space Opera") just by passing a different JSON/Pydantic configuration, preventing hardcoded constraints.

### 4.3 Multimodal Asset Generation (Matplotlib/Pillow)
*   **Decision:** The generator will programmatically generate charts and images matching the dynamic aesthetic (e.g., "diagnostic readouts", "typed guild ledgers") using native Python libraries instead of AI image generation.
*   **Rationale:** Ensures exact numerical alignment between the generated text, the knowledge graph, and the visual assets, which is critical for Multimodal RAG evaluation.

### 4.4 Azure AI Foundry Integration
*   **Decision:** LLM generation will be handled through Azure AI Foundry (Azure OpenAI) via Langchain.
*   **Rationale:** Provides enterprise-grade rate-limiting, security, and access to state-of-the-art models like GPT-4o with Provisioned Throughput Units (PTU) support if scaling to massive generation runs.

## 5. Consequences
*   **Positive:** Zero data leakage. High precision evaluation for RAG multi-hop capability. Highly reusable across different fictional universes.
*   **Negative:** Requires strict schema enforcement before generation. LLM prompts must be highly constrained to avoid breaking the graph logic.


## 4. Document Variety & Formatting (Phase 2 & 3)
* **Decision:** We will inject varied document types (Contracts, Smuggler's Diaries, Letters of Grievance, Ledgers) dynamically into the LLM system prompt.
* **Rationale:** A monolithic dataset of purely "Technical Manuals" limits the capabilities of RAG evaluation. By diversifying the mediums, we stress-test the RAG system's ability to extract graph facts from wildly different semantic structures and tones.

## 5. Competition Corpus Decisions (Phase 7)

### 5.1 Fact Placement over Ego-Graph Dumps
* **Decision:** Documents are compiled from planner-assigned fact lists, never from the focal node's ego-graph.
* **Rationale:** Ego-graph dumps let a single retrieved document (the bridge entity's page) answer "multi-hop" questions, invalidating track 1B. Placement is the only mechanism that can guarantee a question genuinely requires N retrievals.

### 5.2 Programmatic Fact Visuals, Generative Atmosphere
* **Decision:** Any visual that carries a ground-truth number is rendered with matplotlib; gpt-image-2 is used only for decorative franchise art (portraits, heraldry, landscapes) that carries no facts.
* **Rationale:** Diffusion models garble digits; a 1A question keyed to a number "only in pixels" is only fair if those pixels are guaranteed correct. (This restores the original §4.3 decision, which the Phase 5/6 implementation had drifted away from.)

### 5.3 Authority Tiers for Disputed Facts
* **Decision:** Every disputed fact has its true value only in tier-1 canon (codex/annals), the false claim only in tier-3 ephemera, and a "contested" flag (no value) on the wiki.
* **Rationale:** Track 1C requires corroborative, authority-weighing search. If truth and rumor share a document, one retrieval resolves the conflict and the track collapses.

### 5.4 Public / Answer-Key Separation
* **Decision:** The run directory is split into `public/` (documents, images, sample questions) and `answer_key/` (graph, placement matrix, benchmarks, reports). Only `public/` is ever distributed.
* **Rationale:** The old layout mixed ground truth and corpus in one tree; a single packaging mistake would hand teams the solution.
