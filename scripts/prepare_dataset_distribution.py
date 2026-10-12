#!/usr/bin/env python3
"""
scripts/prepare_dataset_distribution.py

Prepares clean distribution packages for publishing the Synthlore benchmark corpus
to Hugging Face Datasets and Kaggle Datasets.

Outputs:
  dist/
    huggingface/
      README.md (Dataset Card with YAML metadata)
      dev.jsonl
      eval.jsonl
      sample_questions.jsonl
      corpus/ (full 415 documents and image assets)
      synthlore_corpus.tar.gz
    kaggle/
      dataset-metadata.json
      README.md
      benchmark/ (dev.json, eval.json, sample_questions.json)
      corpus/ (full 415 documents and image assets)
      synthlore_rag_benchmark.zip
"""

import os
import sys
import json
import shutil
import tarfile
import zipfile
from pathlib import Path


def load_json(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_jsonl(records, path: Path):
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def build_huggingface_card() -> str:
    return """---
language:
- en
license: apache-2.0
size_categories:
- 1K<n<10K
task_categories:
- question-answering
task_ids:
- open-domain-qa
tags:
- rag
- retrieval-augmented-generation
- multi-hop-reasoning
- multimodal
- conflict-resolution
- synthetic-data
- evaluation-benchmark
dataset_info:
  features:
  - name: qid
    dtype: string
  - name: track
    dtype: string
  - name: subtype
    dtype: string
  - name: question
    dtype: string
  - name: answer
    dtype: string
  - name: answer_note
    dtype: string
  - name: reasoning_path
    sequence: string
  - name: expected_evidence
    sequence: string
  - name: ground_truth_fact
    dtype: string
  - name: verified
    dtype: bool
  - name: split
    dtype: string
  splits:
  - name: dev
    num_examples: 20
  - name: eval
    num_examples: 50
pretty_name: "Synthlore: The Ashen Era RAG Benchmark"
---

# Synthlore: The Ashen Era Synthetic RAG Benchmark

Synthlore is a mathematically constrained synthetic benchmark designed to evaluate Retrieval-Augmented Generation (RAG) and agentic search architectures. It pairs an interconnected 415-document (~511,000 words) multi-format fictional corpus (*The Ashen Era*) with 70 verified reasoning questions.

Because the world was synthesized from an isolated causal multigraph, it guarantees **zero pre-training contamination** while testing capabilities that naive benchmarks struggle to isolate.

## Benchmark Tracks

| Track | Target Capability | Architecture Invariant | Questions |
| :--- | :--- | :--- | :--- |
| **Track 1A: Multimodal RAG** | Numerical reasoning over charts and vision-attribute extraction | Ground-truth numbers are omitted from text prompts and plotted into programmatic figure plates (`matplotlib`). Artistic heraldry/portraits (`gpt-image-2`) are verified via a Vision LLM gate. | 38 (11 dev / 27 eval) |
| **Track 1B: Multi-Hop Reasoning** | Connecting facts across disparate documents without shortcuts | For every 2-hop chain $(A \\to e_1 \\to B \\to e_2 \\to C)$, the planner strictly enforces non-cohabitation: `assigned_docs(e_1) ∩ assigned_docs(e_2) = ∅`. Bridge documents cannot resolve the query in a single hop. | 24 (7 dev / 17 eval) |
| **Track 1C: Agentic Conflict Resolution** | Evaluating conflicting claims by weighing source authority | Ground truth is placed in Tier-1 Canon (Codex/Annals), false claims in Tier-3 Ephemera (letters/rumors), and Tier-2 Wiki documents record the dispute without stating a value. | 8 (2 dev / 6 eval) |

## Corpus Breakdown

The corpus comprises 415 documents across multiple real-world business and narrative formats:
- **`codex/`** (63 documents): Official annals, decrees, and lore codexes (PDF & DOCX) with embedded figure plates.
- **`chronicles/`** (50 documents): Long-form narrative history and chronicles (PDF & DOCX).
- **`wiki/`** (95 documents): Collaborative fan-wiki articles (Markdown) with linked figures.
- **`ephemera/`** (147 documents): In-world correspondence, field dispatches, ledgers, and rumors (TXT, DOCX, scanned PDF).
- **`images/`** (85 plates): High-resolution charts, threat matrices, and heraldic banners.

## Dataset Structure

- `dev.jsonl`: 20 development questions with ground truth answers, reasoning chains, and expected evidence files.
- `eval.jsonl`: 50 evaluation questions for held-out pipeline scoring.
- `sample_questions.jsonl`: Blind question prompts without answer keys.
- `synthlore_corpus.tar.gz` (or `corpus/` folder): Complete multi-format document corpus and figure plates.

## Quick Start with Python

```python
from datasets import load_dataset

# Load benchmark question splits
dataset = load_dataset("NavinYP/synthlore-benchmark")
print(dataset["dev"][0])
```

## Citation & Codebase

The generator engine, planners, compilers, and verification suite are open source:
- **GitHub Repository:** [https://github.com/NavinYP/synthlore](https://github.com/NavinYP/synthlore)
- **License:** Apache 2.0
"""


def build_kaggle_metadata() -> dict:
    return {
        "title": "Synthlore: Multi-Hop & Multimodal RAG Benchmark",
        "id": "navinyp/synthlore-rag-benchmark",
        "licenses": [{"name": "apache-2.0"}],
        "description": "A synthetic evaluation corpus of 415 multi-format documents (PDF, DOCX, Markdown, TXT) and 85 visual plates with 70 verified multi-hop, multimodal, and conflict-resolution questions."
    }


def main():
    root = Path(__file__).resolve().parent.parent
    run_dir = root / "output" / "competition_20260826_060502"
    if not run_dir.exists():
        print(f"Error: Run directory {run_dir} not found.")
        sys.exit(1)

    dist_dir = root / "dist"
    hf_dir = dist_dir / "huggingface"
    kaggle_dir = dist_dir / "kaggle"

    # Reset clean dist directories
    for d in [hf_dir, kaggle_dir]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    print("=== 1. Preparing Benchmark Splits ===")
    answer_key = run_dir / "answer_key"
    public_dir = run_dir / "public"

    dev_data = load_json(answer_key / "benchmark_dev.json")
    eval_data = load_json(answer_key / "benchmark_eval.json")
    sample_data = load_json(public_dir / "sample_questions.json")

    # Write Hugging Face files
    save_jsonl(dev_data, hf_dir / "dev.jsonl")
    save_jsonl(eval_data, hf_dir / "eval.jsonl")
    save_jsonl(sample_data, hf_dir / "sample_questions.jsonl")
    (hf_dir / "README.md").write_text(build_huggingface_card(), encoding="utf-8")
    print(f"  [HF] Saved dev.jsonl ({len(dev_data)}), eval.jsonl ({len(eval_data)}), README.md")

    # Write Kaggle files
    kaggle_bench = kaggle_dir / "benchmark"
    kaggle_bench.mkdir(parents=True, exist_ok=True)
    with open(kaggle_bench / "benchmark_dev.json", "w", encoding="utf-8") as f:
        json.dump(dev_data, f, indent=2)
    with open(kaggle_bench / "benchmark_eval.json", "w", encoding="utf-8") as f:
        json.dump(eval_data, f, indent=2)
    with open(kaggle_bench / "sample_questions.json", "w", encoding="utf-8") as f:
        json.dump(sample_data, f, indent=2)
    with open(kaggle_dir / "dataset-metadata.json", "w", encoding="utf-8") as f:
        json.dump(build_kaggle_metadata(), f, indent=2)
    (kaggle_dir / "README.md").write_text(build_huggingface_card(), encoding="utf-8")
    print(f"  [Kaggle] Saved benchmark JSONs and dataset-metadata.json")

    print("\n=== 2. Copying Public Corpus (415 docs + images) ===")
    for target_parent, name in [(hf_dir, "corpus"), (kaggle_dir, "corpus")]:
        target_corpus = target_parent / name
        target_corpus.mkdir(parents=True, exist_ok=True)
        for folder in ["chronicles", "codex", "wiki", "ephemera", "images"]:
            src = public_dir / folder
            dst = target_corpus / folder
            if src.exists():
                shutil.copytree(src, dst)
        if (public_dir / "README.txt").exists():
            shutil.copy2(public_dir / "README.txt", target_corpus / "README.txt")
        print(f"  Copied corpus into {target_corpus}")

    print("\n=== 3. Packaging Archives for Web / CLI Upload ===")
    hf_archive = hf_dir / "synthlore_corpus.tar.gz"
    print(f"  Creating {hf_archive.name}...")
    with tarfile.open(hf_archive, "w:gz") as tar:
        tar.add(hf_dir / "corpus", arcname="corpus")

    kaggle_archive = dist_dir / "synthlore_rag_benchmark.zip"
    print(f"  Creating {kaggle_archive.name}...")
    with zipfile.ZipFile(kaggle_archive, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root_p, dirs, files in os.walk(kaggle_dir):
            for file in files:
                full_p = Path(root_p) / file
                rel_p = full_p.relative_to(kaggle_dir)
                zipf.write(full_p, arcname=str(rel_p))

    print("\n=== Packaging Complete! ===")
    print(f"  Hugging Face Distribution : {hf_dir} ({sum(f.stat().st_size for f in hf_dir.rglob('*') if f.is_file()) / (1024*1024):.1f} MB)")
    print(f"  Kaggle Distribution       : {kaggle_dir} ({sum(f.stat().st_size for f in kaggle_dir.rglob('*') if f.is_file()) / (1024*1024):.1f} MB)")
    print(f"  Kaggle Ready Zip Archive  : {kaggle_archive} ({kaggle_archive.stat().st_size / (1024*1024):.1f} MB)")


if __name__ == "__main__":
    main()
