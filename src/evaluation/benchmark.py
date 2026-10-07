"""Benchmark builder for the competition.

Questions are derived directly from the planner's protected structures, so by
construction each track tests what it claims to test:
- 1A questions key on visual-only facts (the value exists in exactly one
  figure plate and in no text document).
- 1B questions key on protected chains (the two hops never share a document).
- 1C questions key on disputed facts (false claim in tier-3 ephemera, truth
  only in tier-1 canon).

Answers and provenance are composed programmatically from ground truth; the
reasoning model only PHRASES the question. Each item is then verified against
the actual generated corpus text before it can enter the benchmark, and the
set is split into a releasable dev set and a held-out eval set.
"""
import asyncio
import json
import random
import re
from typing import Dict, Any, List, Optional

import networkx as nx

from src.planning.corpus_planner import fact_to_text, CHAIN_TEMPLATES
from src.evaluation.leakcheck import leak_near, value_owners

PHRASE_SYSTEM = (
    "You write benchmark questions for a document-QA competition set in a fictional "
    "grimdark fantasy corpus. Output pure JSON: {\"question\": \"...\"}. The question "
    "must be natural, specific, and answerable ONLY from the described evidence."
)


def _parse_question(raw: str) -> Optional[str]:
    try:
        m = re.search(r"\{.*\}", raw, re.DOTALL)
        return json.loads(m.group(0) if m else raw).get("question")
    except Exception:
        return None


class BenchmarkBuilder:
    def __init__(self, llm, G: nx.MultiDiGraph, plan: Dict[str, Any],
                 doc_texts: Dict[str, str], doc_files: Dict[str, str], seed: int = 7,
                 atmo_verification: Dict[str, Any] = None):
        self.llm = llm
        self.G = G
        self.plan = plan
        self.doc_texts = doc_texts
        self.doc_files = doc_files
        self.rng = random.Random(seed)
        self.facts = plan["facts"]
        self.atmo_verification = atmo_verification or {}

    def _name(self, n: str) -> str:
        return self.G.nodes[n]["name"]

    def _files(self, doc_ids: List[str]) -> List[str]:
        return [self.doc_files[d] for d in doc_ids if d in self.doc_files]

    async def _phrase(self, instruction: str, fallback: str) -> str:
        try:
            raw = await self.llm.synthesize_reasoning(instruction, PHRASE_SYSTEM)
            return _parse_question(raw) or fallback
        except Exception:
            return fallback

    # ------------------------------------------------------------- track 1A

    async def _item_1a(self, i: int, fid: str) -> Dict[str, Any]:
        fact = self.facts[fid]
        fig = self.plan["figures"][fact["figure"]]
        entity_name = self._name(fact["subject"])
        prop_h = fact["prop"].replace("_", " ")
        fallback = f"According to the codex plate for {entity_name}, what is its recorded {prop_h}?"
        question = await self._phrase(
            f"The corpus contains a figure plate recording the {prop_h} of the entity "
            f"'{entity_name}'. This number appears ONLY in that image, never in text. "
            f"Write ONE question that requires reading the plate to answer.",
            fallback,
        )
        host_files = self._files([fig["host_doc"]])
        return {
            "qid": f"1a_{i:03d}", "track": "1A_multimodal",
            "question": question,
            "answer": str(fact["value"]),
            "answer_aliases": sorted({str(fact["value"]), f"{fact['value']:,}"}),
            "answer_note": f"The {prop_h} of {entity_name} is {fact['value']}; stated only in figure plate {fig['filename']}.",
            "reasoning_path": [entity_name],
            "expected_evidence": host_files + [f"images/{fig['filename']}"],
            "ground_truth_fact": fact_to_text(fact, self.G),
        }

    def _item_1a_visual(self, i: int, v: Dict[str, Any]) -> Dict[str, Any]:
        """Question on a vision-verified controlled attribute of an atmospheric image."""
        return {
            "qid": f"1a_v{i:02d}", "track": "1A_multimodal", "subtype": "visual_attribute",
            "question": v["question"],
            "answer": v["answer"],
            "answer_note": (f"The image {v['filename']} was generated with, and vision-verified to "
                            f"contain, {v['detail']}. The detail exists only in the image."),
            "reasoning_path": [v["entity_name"]],
            "expected_evidence": self._files([v["host_doc"]]) + [f"wiki/images/{v['filename']}"],
            "ground_truth_fact": f"{v['entity_name']} - {v['slot']}: {v['answer']} (visual only)",
        }

    def mine_extra_chains(self, limit: int) -> List[Dict[str, Any]]:
        """Find additional 2-hop chains whose hops ALREADY live in disjoint documents.

        The planner protects a fixed chain set at placement time; with
        redundancy-2 placement many other chains end up split across documents
        anyway. Those can safely become extra 1B questions post-hoc, without
        touching the corpus - disjointness is enforced here exactly as the
        planner enforces it (the two hops share no document).
        """
        used_pairs = {(c["a"], c["c"]) for c in self.plan["chains"]}
        edge_index: Dict[tuple, List[Dict[str, Any]]] = {}
        for f in self.facts.values():
            if f["kind"] == "edge":
                edge_index.setdefault((f["u"], f["relation"]), []).append(f)

        def direct_link(a, c):
            return self.G.has_edge(a, c) or self.G.has_edge(c, a)

        mined = []
        for f1 in self.facts.values():
            if len(mined) >= limit:
                break
            if f1["kind"] != "edge" or not f1.get("assigned_docs"):
                continue
            for rel1, rel2 in CHAIN_TEMPLATES:
                if f1["relation"] != rel1:
                    continue
                for f2 in edge_index.get((f1["v"], rel2), []):
                    a, c = f1["u"], f2["v"]
                    if a == c or (a, c) in used_pairs or direct_link(a, c):
                        continue
                    docs1 = set(f1.get("assigned_docs", []))
                    docs2 = set(f2.get("assigned_docs", []))
                    if not docs1 or not docs2 or (docs1 & docs2):
                        continue
                    used_pairs.add((a, c))
                    mined.append({
                        "chain_id": f"xchain_{len(mined):03d}",
                        "a": a, "bridge": f1["v"], "c": c,
                        "edge1": f1["fact_id"], "edge2": f2["fact_id"],
                        "docs_edge1": sorted(docs1), "docs_edge2": sorted(docs2),
                        "template": f"{rel1}+{rel2}", "mined": True,
                    })
                    if len(mined) >= limit:
                        break
        return mined

    async def _item_warmup(self, i: int, fact: Dict[str, Any]) -> Dict[str, Any]:
        """Single-fact warm-up question. Released in the dev set only, never judged -
        it lets teams sanity-check their retrieval before the hard tracks."""
        name = self._name(fact["subject"])
        prop_h = fact["prop"].replace("_", " ")
        val = str(fact["value"])
        if fact["prop"] in ("born", "died", "founded", "forged", "began", "ended"):
            val += " AS"
        fallback = f"What is the {prop_h} of {name}?"
        question = await self._phrase(
            f"Ground truth: {fact_to_text(fact, self.G)}. Write ONE simple, direct factual "
            f"question about '{name}' whose answer is exactly this value. Do not reveal the value.",
            fallback,
        )
        return {
            "qid": f"warmup_{i:03d}", "track": "warmup_factual",
            "question": question, "answer": val,
            "reasoning_path": [name],
            "expected_evidence": self._files(fact.get("assigned_docs", [])),
            "ground_truth_fact": fact_to_text(fact, self.G),
        }

    # ------------------------------------------------------------- track 1B

    async def _item_1b(self, i: int, chain: Dict[str, Any]) -> Dict[str, Any]:
        e1, e2 = self.facts[chain["edge1"]], self.facts[chain["edge2"]]
        a, b, c = self._name(chain["a"]), self._name(chain["bridge"]), self._name(chain["c"])
        hop1, hop2 = fact_to_text(e1, self.G), fact_to_text(e2, self.G)
        fallback = f"What connects {a} to {c}?"
        question = await self._phrase(
            f"Ground truth (two facts stored in DIFFERENT documents):\n"
            f"  Hop 1: {hop1}\n  Hop 2: {hop2}\n"
            f"Write ONE question about the connection between '{a}' and '{c}'. "
            f"HARD RULE: the question must NOT mention '{b}' or hint at it. "
            f"The answer requires combining both hops.",
            fallback,
        )
        return {
            "qid": f"1b_{i:03d}", "track": "1B_multihop",
            "question": question,
            "answer": f"Via {b}: {hop1}; and {hop2}.",
            "reasoning_path": [a, b, c],
            "expected_evidence": self._files(chain["docs_edge1"]) + self._files(chain["docs_edge2"]),
            "ground_truth_fact": f"{hop1} | {hop2}",
            "bridge_entity": b,
        }

    # ------------------------------------------------------------- track 1C

    async def _item_1c(self, i: int, dispute: Dict[str, Any]) -> Dict[str, Any]:
        name = dispute["entity_name"]
        prop_h = dispute["property"].replace("_", " ")
        fallback = f"Sources disagree about the {prop_h} year of {name}. What is the correct year, and which source is authoritative?"
        question = await self._phrase(
            f"In the corpus, low-authority documents (ballads, letters, broadsheets) claim the "
            f"{prop_h} year of '{name}' is {dispute['false_value']} AS, while the canonical codex "
            f"records {dispute['true_value']} AS. Write ONE question asking for the TRUE {prop_h} "
            f"year of '{name}'. HARD RULES: the question must ask for the actual/correct year - "
            f"never what a particular source claims; do NOT use the phrase 'according to'; do NOT "
            f"invent or name any source or document; do NOT reveal either year.",
            fallback,
        )
        # Guard: a question anchored to a source would make the FALSE value the
        # technically correct reading, contradicting the answer key.
        if "according to" in question.lower():
            question = fallback
        return {
            "qid": f"1c_{i:03d}", "track": "1C_agentic",
            "question": question,
            "answer": f"{dispute['true_value']} AS",
            "answer_note": (f"Unreliable sources claim {dispute['false_value']} AS; the canonical codex "
                            f"entry records {dispute['true_value']} AS and is authoritative."),
            "reasoning_path": [name],
            "expected_evidence": self._files([dispute["canon_doc"]] + dispute.get("false_docs", [])),
            "distractor_value": str(dispute["false_value"]),
            "ground_truth_fact": f"{name} - {prop_h}: {dispute['true_value']} AS",
        }

    # ----------------------------------------------------------- verification

    def _verify(self, item: Dict[str, Any]) -> bool:
        """The supporting evidence must actually exist in the generated corpus."""
        track = item["track"]
        base = lambda n: re.split(r" the ", n, maxsplit=1)[0].lower()
        if item.get("subtype") == "visual_attribute":
            # The attribute answer must not be guessable from text: reject if the
            # answer phrase appears near the entity in any text document.
            ent = base(item["reasoning_path"][0])
            return not any(leak_near(text, ent, item["answer"])
                           for text in self.doc_texts.values())
        if track == "1A_multimodal":
            # Figure plates are programmatic, so the value is present by construction;
            # verify the value is never stated near (and attributed to) the entity in
            # any text document. Rival owners of the same value absorb coincidences.
            entity = base(item["reasoning_path"][0])
            subject = next((f["subject"] for f in self.facts.values()
                            if f.get("figure") and self._name(f["subject"]) == item["reasoning_path"][0]), None)
            try:
                rivals = value_owners(self.G, int(item["answer"]), exclude_node=subject)
            except ValueError:
                rivals = []
            return not any(leak_near(text, entity, item["answer"], rival_names=rivals)
                           for text in self.doc_texts.values())
        if track == "1B_multihop":
            a, b, c = item["reasoning_path"]
            # Each hop's names must appear in the evidence docs.
            docs = [d for d, f in self.doc_files.items() if f in item["expected_evidence"]]
            joined = "\n".join(self.doc_texts.get(d, "") for d in docs).lower()
            return all(base(n) in joined for n in (a, b, c))
        if track == "1C_agentic":
            docs = [d for d, f in self.doc_files.items() if f in item["expected_evidence"]]
            joined = "\n".join(self.doc_texts.get(d, "") for d in docs)
            true_v = item["answer"].split(" ")[0]
            return true_v in joined and item["distractor_value"] in joined
        if track == "warmup_factual":
            docs = [d for d, f in self.doc_files.items() if f in item["expected_evidence"]]
            joined = "\n".join(self.doc_texts.get(d, "") for d in docs).lower()
            val = item["answer"].replace(" AS", "").lower()
            return bool(docs) and base(item["reasoning_path"][0]) in joined and val in joined
        return False

    # ----------------------------------------------------------------- build

    async def build(self, dev_ratio: float = 0.3, concurrency: int = 2,
                    extra_chains: int = 0, warmups: int = 0) -> Dict[str, Any]:
        sem = asyncio.Semaphore(concurrency)

        async def guarded(coro):
            async with sem:
                return await coro

        chains = list(self.plan["chains"]) + self.mine_extra_chains(extra_chains)

        # Warm-up candidates: placed property facts that carry no spoilers.
        disputed = {f"prop:{d['entity']}:{d['property']}" for d in self.plan["disputes"]}
        warm_cand = [f for f in self.facts.values()
                     if f["kind"] == "property" and f.get("assigned_docs")
                     and f["fact_id"] not in disputed
                     and f["prop"] not in ("secret", "secret_truth")]
        self.rng.shuffle(warm_cand)

        tasks = []
        for i, fid in enumerate(self.plan["visual_only"]):
            tasks.append(guarded(self._item_1a(i, fid)))
        for i, chain in enumerate(chains):
            tasks.append(guarded(self._item_1b(i, chain)))
        for i, dispute in enumerate(self.plan["disputes"]):
            tasks.append(guarded(self._item_1c(i, dispute)))
        for i, fact in enumerate(warm_cand[:warmups]):
            tasks.append(guarded(self._item_warmup(i, fact)))
        items = list(await asyncio.gather(*tasks))

        verified_attrs = [v for v in self.atmo_verification.values() if v.get("verified")]
        items += [self._item_1a_visual(i, v) for i, v in enumerate(verified_attrs)]

        for item in items:
            item["verified"] = self._verify(item)

        usable = [x for x in items if x["verified"]]
        rejected = [x for x in items if not x["verified"]]

        # Stratified dev/eval split per track; warm-ups are dev-only by design.
        dev, evalset = [], []
        for track in ("1A_multimodal", "1B_multihop", "1C_agentic"):
            group = [x for x in usable if x["track"] == track]
            self.rng.shuffle(group)
            k = max(1, int(len(group) * dev_ratio)) if group else 0
            dev += group[:k]
            evalset += group[k:]
        dev += [x for x in usable if x["track"] == "warmup_factual"]
        for x in dev:
            x["split"] = "dev"
        for x in evalset:
            x["split"] = "eval"

        return {"dev": dev, "eval": evalset, "rejected": rejected}
