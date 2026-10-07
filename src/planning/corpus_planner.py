"""CorpusPlanner: decides WHICH facts appear in WHICH documents.

This is the piece the old pipeline lacked. Previously every document dumped the
full ego-graph of its focal node, which meant:
  - multi-hop (1B) questions leaked through the bridge entity's own page,
  - multimodal (1A) facts also existed in text,
  - agentic (1C) contradictions sat next to the truth in the same file.

The planner enumerates every ground-truth fact, builds the document plan
(chronicle chapters, wiki articles, codex entries, ephemera), and assigns each
fact to specific documents under three hard constraints:

  1A  VISUAL-ONLY: selected numeric facts are excluded from every text context
      and rendered only into programmatic figure plates.
  1B  SPLIT CHAINS: for each protected 2-hop chain, the two edge facts never
      co-occur in any single document.
  1C  AUTHORITY TIERS: a disputed fact's true value lives only in tier-1 canon
      (codex); the false claim lives only in tier-3 ephemera; the wiki flags
      the dispute without resolving it.

The resulting placement matrix is both the compiler input and the answer-key
provenance map.
"""
import random
from typing import Dict, Any, List, Tuple, Optional

import networkx as nx

PROPERTY_FACTS = {
    "character": ["role", "born", "died", "secret"],
    "location": ["region", "founded", "garrison_strength", "status"],
    "artifact": ["artifact_class", "forged", "attunement_cost"],
    "conflict": ["began", "ended", "casualty_figure", "outcome", "secret_truth", "victor"],
    "creature": ["threat_rating", "habit"],
    "faction": ["doctrine", "org_kind"],
}

VISUAL_CANDIDATE_PROPS = {"garrison_strength", "casualty_figure", "attunement_cost", "threat_rating"}

CHAIN_TEMPLATES = [
    ("WIELDS", "HOUSED_IN"),
    ("WIELDS", "FORGED_AT"),
    ("MEMBER_OF", "VICTOR_OF"),
    ("COMMANDS", "RULED_BY"),
    ("DEVASTATED", "RULED_BY"),
    ("LAIRS_IN", "RULED_BY"),
    ("SLEW", "MEMBER_OF"),
    ("MENTOR_OF", "FOUGHT_IN"),
    ("SERVES_AT", "RULED_BY"),
]

EPHEMERA_KINDS = [
    "letter", "decree", "quartermaster ledger", "trial transcript", "ballad",
    "field report", "sermon", "contract", "interrogation record", "muster roll",
    "petition", "auction catalogue",
]

EPHEMERA_FORMATS = [".txt", ".txt", ".docx", ".docx", ".pdf", ".pdf", ".scan.pdf"]

# Controlled visual attributes: a concrete detail injected into the image prompt,
# verified after generation by the vision model, and (only if verified) turned
# into a track-1A visual question. Answers are single concrete nouns/phrases so
# grading stays clean. These details exist ONLY in pixels - never in text.
VISUAL_ATTRIBUTE_BANK = {
    "portrait": [
        {"slot": "shoulder bird", "detail": "a {x} perched on their shoulder",
         "options": ["raven", "kestrel", "white owl"],
         "question": "In the portrait of {name}, what bird is perched on their shoulder?"},
        {"slot": "held object", "detail": "holding a {x} in one hand",
         "options": ["lantern", "chalice", "scroll", "war-hammer"],
         "question": "In the portrait of {name}, what object are they holding?"},
        {"slot": "headwear", "detail": "wearing a {x} on their head",
         "options": ["circlet of black iron", "crown of antlers", "hood of grey wolf-fur"],
         "question": "In the portrait of {name}, what do they wear on their head?"},
    ],
    "heraldry": [
        {"slot": "central emblem", "detail": "the central emblem of the banner is a {x}",
         "options": ["stag skull", "coiled serpent", "burning tower", "crossed keys", "weeping eye"],
         "question": "What is the central emblem on the banner of {name}?"},
    ],
    "relic": [
        # Note: avoid words grimdark prose uses constantly (skull, blood, ash) -
        # they collide with chapter text and get their questions rejected.
        {"slot": "engraved motif", "detail": "engraved with a prominent {x} motif",
         "options": ["serpent", "sunburst", "moth", "rose"],
         "question": "What motif is engraved on {name} in its official illustration?"},
    ],
}


def fact_to_text(fact: Dict[str, Any], G: nx.MultiDiGraph) -> str:
    """Render a fact as an unambiguous ground-truth line for LLM prompts."""
    if fact["kind"] == "property":
        name = G.nodes[fact["subject"]]["name"]
        prop = fact["prop"].replace("_", " ")
        val = fact["value"]
        if fact["prop"] in ("born", "died", "founded", "forged", "began", "ended"):
            return f"{name} - {prop}: {val} AS"
        return f"{name} - {prop}: {val}"
    u_name = G.nodes[fact["u"]]["name"]
    v_name = G.nodes[fact["v"]]["name"]
    rel = fact["relation"].replace("_", " ").lower()
    attrs = fact.get("attrs") or {}
    suffix = ""
    if "year" in attrs:
        suffix = f" (in {attrs['year']} AS)"
    elif "since" in attrs:
        suffix = f" (since {attrs['since']} AS)"
    if "side" in attrs:
        suffix += f" [fighting for {attrs['side']}]"
    return f"{u_name} {rel} {v_name}{suffix}"


class CorpusPlanner:
    def __init__(self, G: nx.MultiDiGraph, disputes: List[Dict[str, Any]],
                 seed: int = 7, scale: Optional[Dict[str, Any]] = None):
        self.G = G
        self.disputes = disputes
        self.rng = random.Random(seed)
        self.scale = {
            "volumes": 4,
            "chapters_per_volume": 15,
            "chapter_words": 4200,
            "wiki_words": 1000,
            "codex_entry_words": 380,
            "ephemera_docs": 150,
            "ephemera_words": 420,
            "visual_only_facts": 15,
            "protected_chains": 24,
            "fact_redundancy": 2,
        }
        if scale:
            self.scale.update(scale)

        self.facts: Dict[str, Dict[str, Any]] = {}
        self.docs: Dict[str, Dict[str, Any]] = {}
        self.figures: Dict[str, Dict[str, Any]] = {}
        self.atmo_images: Dict[str, Dict[str, Any]] = {}
        self.chains: List[Dict[str, Any]] = []
        self.visual_only: List[str] = []

    # ------------------------------------------------------------- utilities

    def _kind(self, n: str) -> str:
        return self.G.nodes[n]["kind"]

    def _name(self, n: str) -> str:
        return self.G.nodes[n]["name"]

    def _nodes(self, kind: str, **filters) -> List[str]:
        out = []
        for n, d in self.G.nodes(data=True):
            if d["kind"] != kind:
                continue
            if all(d.get(k) == v for k, v in filters.items()):
                out.append(n)
        return out

    # ------------------------------------------------------------ fact model

    def _enumerate_facts(self):
        for n, d in self.G.nodes(data=True):
            for prop in PROPERTY_FACTS.get(d["kind"], []):
                if prop in d:
                    fid = f"prop:{n}:{prop}"
                    self.facts[fid] = {"fact_id": fid, "kind": "property",
                                       "subject": n, "prop": prop, "value": d[prop]}
        for u, v, key, d in self.G.edges(keys=True, data=True):
            fid = f"edge:{u}:{d['relation']}:{v}:{key}"
            attrs = {k: val for k, val in d.items() if k != "relation"}
            self.facts[fid] = {"fact_id": fid, "kind": "edge", "u": u, "v": v,
                               "relation": d["relation"], "attrs": attrs}

    def _select_visual_only(self):
        """Numeric facts that will exist ONLY inside figure plates (track 1A)."""
        disputed = {(d["entity"], d["property"]) for d in self.disputes}
        candidates = [f for f in self.facts.values()
                      if f["kind"] == "property"
                      and f["prop"] in VISUAL_CANDIDATE_PROPS
                      and (f["subject"], f["prop"]) not in disputed]
        self.rng.shuffle(candidates)
        for f in candidates[: self.scale["visual_only_facts"]]:
            f["channel"] = "visual_only"
            self.visual_only.append(f["fact_id"])

    def _select_chains(self):
        """Protected 2-hop chains A -> B -> C for track 1B."""
        edge_index: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        for f in self.facts.values():
            if f["kind"] != "edge":
                continue
            edge_index.setdefault((f["u"], f["relation"]), []).append(f)

        def direct_link(a: str, c: str) -> bool:
            return self.G.has_edge(a, c) or self.G.has_edge(c, a)

        seen_pairs = set()
        candidates = []
        for f1 in self.facts.values():
            if f1["kind"] != "edge":
                continue
            for rel1, rel2 in CHAIN_TEMPLATES:
                if f1["relation"] != rel1:
                    continue
                bridge = f1["v"]
                for f2 in edge_index.get((bridge, rel2), []):
                    a, c = f1["u"], f2["v"]
                    if a == c or direct_link(a, c):
                        continue
                    pair = (a, c)
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    candidates.append({
                        "chain_id": f"chain_{len(candidates):03d}",
                        "a": a, "bridge": bridge, "c": c,
                        "edge1": f1["fact_id"], "edge2": f2["fact_id"],
                        "template": f"{rel1}+{rel2}",
                    })
        self.rng.shuffle(candidates)
        self.chains = candidates[: self.scale["protected_chains"]]
        chain_edges = set()
        for ch in self.chains:
            chain_edges.add(ch["edge1"])
            chain_edges.add(ch["edge2"])
        for fid in chain_edges:
            self.facts[fid]["in_chain"] = True

    # -------------------------------------------------------------- doc plan

    def _add_doc(self, doc_id: str, **spec) -> Dict[str, Any]:
        spec.setdefault("facts", [])
        spec.setdefault("false_claims", [])
        spec.setdefault("figures", [])
        spec.setdefault("images", [])
        spec["doc_id"] = doc_id
        self.docs[doc_id] = spec
        return spec

    def _plan_chronicles(self):
        conflicts = sorted(self._nodes("conflict"), key=lambda c: self.G.nodes[c]["began"])
        majors = self._nodes("character", tier="major")
        volumes = self.scale["volumes"]
        per_vol = self.scale["chapters_per_volume"]
        vol_titles = ["The Kindling Years", "The Long Reprisal",
                      "A Crown of Cinders", "The Silent Accounting",
                      "The Last Vigil", "Embers of the Accord"]
        for v in range(volumes):
            # Each volume leans on a slice of the conflict timeline.
            vol_conflicts = conflicts[v * len(conflicts) // volumes:
                                      (v + 1) * len(conflicts) // volumes] or conflicts
            book = f"The Ashen Chronicles, Volume {['I','II','III','IV','V','VI'][v]}: {vol_titles[v % len(vol_titles)]}"
            for ch in range(per_vol):
                conflict = vol_conflicts[ch % len(vol_conflicts)]
                fighters = [u for u, t, d in self.G.in_edges(conflict, data=True)
                            if d.get("relation") == "FOUGHT_IN" and self.G.nodes[u]["tier"] == "major"]
                pov = fighters[ch % len(fighters)] if fighters else majors[ch % len(majors)]
                sites = [t for _, t, d in self.G.out_edges(conflict, data=True)
                         if d.get("relation") in ("WAGED_AT", "DEVASTATED")]
                allies = [t for _, t, d in self.G.out_edges(pov, data=True)
                          if d.get("relation") in ("MENTOR_OF", "RIVAL_OF", "SLEW", "WIELDS")]
                focus = [pov, conflict] + sites[:2] + allies[:3]
                self._add_doc(
                    f"chronicle_v{v+1}_c{ch+1:02d}",
                    kind="chapter", book=book, tier=2,
                    title=f"Chapter {ch+1}",
                    pov=pov, focus=list(dict.fromkeys(focus)),
                    target_words=self.scale["chapter_words"],
                )

    def _plan_wiki(self):
        wiki_entities = (
            self._nodes("character", tier="major")
            + self._nodes("faction")
            + [l for l in self._nodes("location")]
            + self._nodes("artifact")
            + self._nodes("conflict")
            + self._nodes("creature")
        )
        minors = self._nodes("character", tier="minor")
        self.rng.shuffle(minors)
        wiki_entities += minors[: max(0, len(minors) - 15)]  # most, not all, minors get pages
        for n in wiki_entities:
            self._add_doc(
                f"wiki_{n}",
                kind="wiki", tier=1, book=None,
                title=self._name(n), focus=[n],
                target_words=self.scale["wiki_words"],
            )

    def _plan_codex(self):
        for n in self._nodes("location"):
            self._add_doc(f"codex_gaz_{n}", kind="codex_entry", tier=1,
                          book="Codex Vaeloria I: Gazetteer of the Sundered Realms",
                          title=self._name(n), focus=[n],
                          target_words=self.scale["codex_entry_words"])
        for n in self._nodes("artifact") + self._nodes("creature"):
            self._add_doc(f"codex_arm_{n}", kind="codex_entry", tier=1,
                          book="Codex Vaeloria II: Armory of Relics and Bestiary",
                          title=self._name(n), focus=[n],
                          target_words=self.scale["codex_entry_words"])
        for n in self._nodes("conflict") + self._nodes("faction"):
            self._add_doc(f"codex_ann_{n}", kind="codex_entry", tier=1,
                          book="The Annals of the Ashen Era",
                          title=self._name(n), focus=[n],
                          target_words=self.scale["codex_entry_words"])
        # A biographical registry so every character has a tier-1 home.
        for n in self._nodes("character"):
            self._add_doc(f"codex_reg_{n}", kind="codex_entry", tier=1,
                          book="The Annals of the Ashen Era",
                          title=f"Registry: {self._name(n)}", focus=[n],
                          target_words=180)

    def _plan_ephemera(self):
        all_entities = list(self.G.nodes)
        for i in range(self.scale["ephemera_docs"]):
            kind = self.rng.choice(EPHEMERA_KINDS)
            focus = self.rng.sample(all_entities, self.rng.randint(1, 3))
            self._add_doc(
                f"ephemera_{i:03d}",
                kind="ephemera", tier=3, book=None,
                title=f"{kind.title()} concerning {self._name(focus[0])}",
                ephemera_kind=kind,
                fmt=self.rng.choice(EPHEMERA_FORMATS),
                focus=focus,
                target_words=self.scale["ephemera_words"],
            )

    # ------------------------------------------------------------ assignment

    def _docs_focused_on(self, entity: str, kinds: Optional[List[str]] = None) -> List[str]:
        out = []
        for did, spec in self.docs.items():
            if kinds and spec["kind"] not in kinds:
                continue
            if entity in spec["focus"]:
                out.append(did)
        return out

    def _assign_facts(self):
        disputed_ids = {f"prop:{d['entity']}:{d['property']}": d for d in self.disputes}
        redundancy = self.scale["fact_redundancy"]

        for fid, fact in self.facts.items():
            if fact.get("channel") == "visual_only":
                continue  # handled by _assign_figures
            if fid in disputed_ids:
                continue  # handled by _assign_disputes

            subjects = [fact["subject"]] if fact["kind"] == "property" else [fact["u"], fact["v"]]
            # Preferred homes: wiki + codex of the subject, then chapters/ephemera.
            candidates = []
            for s in subjects:
                candidates += self._docs_focused_on(s, kinds=["wiki", "codex_entry"])
            for s in subjects:
                candidates += self._docs_focused_on(s, kinds=["chapter", "ephemera"])
            candidates = list(dict.fromkeys(candidates))
            if not candidates:
                continue
            chosen = candidates[:redundancy]
            # Give chapters a chance to carry edge facts for narrative texture.
            extras = [c for c in candidates[redundancy:] if self.docs[c]["kind"] == "chapter"]
            if extras and self.rng.random() < 0.5:
                chosen.append(self.rng.choice(extras))
            for did in chosen:
                self.docs[did]["facts"].append(fid)
            fact["assigned_docs"] = chosen

        self._enforce_chain_split()
        self._assign_disputes(disputed_ids)
        self._assign_figures()
        self._coverage_pass()

    def _enforce_chain_split(self):
        """Hard 1B constraint: a chain's two edges never share a document."""
        for chain in self.chains:
            e1, e2 = self.facts[chain["edge1"]], self.facts[chain["edge2"]]
            docs1 = set(e1.get("assigned_docs", []))
            docs2 = set(e2.get("assigned_docs", []))
            overlap = docs1 & docs2
            for did in overlap:
                self.docs[did]["facts"].remove(e2["fact_id"])
                docs2.discard(did)
            if not docs2:
                # Re-home edge2 somewhere edge1 does not live.
                fallback = [d for d in self._docs_focused_on(e2["v"], kinds=["wiki", "codex_entry", "ephemera"])
                            + self._docs_focused_on(e2["u"], kinds=["codex_entry", "ephemera"])
                            if d not in docs1]
                if not fallback:
                    fallback = [d for d, s in self.docs.items()
                                if s["kind"] == "ephemera" and d not in docs1]
                target = fallback[0]
                self.docs[target]["facts"].append(e2["fact_id"])
                self.docs[target]["focus"] = list(dict.fromkeys(self.docs[target]["focus"] + [e2["u"], e2["v"]]))
                docs2 = {target}
            e2["assigned_docs"] = sorted(docs2)
            e1["assigned_docs"] = sorted(docs1)
            chain["docs_edge1"] = e1["assigned_docs"]
            chain["docs_edge2"] = e2["assigned_docs"]

    def _assign_disputes(self, disputed_ids: Dict[str, Dict[str, Any]]):
        """1C: truth only in tier-1 canon; false claim only in tier-3 ephemera."""
        ephemera = [d for d, s in self.docs.items() if s["kind"] == "ephemera"]
        for fid, dispute in disputed_ids.items():
            fact = self.facts.get(fid)
            if fact is None:
                continue
            entity = dispute["entity"]
            canon = self._docs_focused_on(entity, kinds=["codex_entry"])
            canon_doc = canon[0] if canon else self._docs_focused_on(entity, kinds=["wiki"])[0]
            self.docs[canon_doc]["facts"].append(fid)
            self.docs[canon_doc].setdefault("canon_notes", []).append(
                f"State plainly that {dispute['entity_name']}'s {dispute['property']} is "
                f"{dispute['true_value']} AS, and note that popular accounts wrongly claim otherwise."
            )
            fact["assigned_docs"] = [canon_doc]

            wiki = self._docs_focused_on(entity, kinds=["wiki"])
            if wiki:
                self.docs[wiki[0]].setdefault("dispute_flags", []).append(
                    f"The {dispute['property']} of {dispute['entity_name']} is contested among sources; "
                    f"do NOT state any year for it - direct readers to the Annals/Codex as the authority."
                )

            hosts = self.rng.sample(ephemera, min(2, len(ephemera)))
            for h in hosts:
                self.docs[h]["false_claims"].append(dispute["dispute_id"])
                self.docs[h]["focus"] = list(dict.fromkeys(self.docs[h]["focus"] + [entity]))
            dispute["canon_doc"] = canon_doc
            dispute["false_docs"] = hosts

    def _assign_figures(self):
        """1A: visual-only facts become programmatic figure plates."""
        styles = ["spec_plate", "tally_chart", "gauge_plate"]
        for i, fid in enumerate(self.visual_only):
            fact = self.facts[fid]
            entity = fact["subject"]
            hosts = (self._docs_focused_on(entity, kinds=["codex_entry"])
                     or self._docs_focused_on(entity, kinds=["wiki"]))
            host = hosts[0]
            figure_id = f"plate_{i:02d}_{entity}"
            self.figures[figure_id] = {
                "figure_id": figure_id,
                "fact_id": fid,
                "entity": entity,
                "entity_name": self._name(entity),
                "prop": fact["prop"],
                "value": fact["value"],
                "style": styles[i % len(styles)],
                "host_doc": host,
                "filename": f"{figure_id}.png",
            }
            self.docs[host]["figures"].append(figure_id)
            fact["assigned_docs"] = []  # never in text
            fact["figure"] = figure_id

    def _coverage_pass(self):
        """Every non-visual fact must live in at least one document."""
        for fid, fact in self.facts.items():
            if fact.get("channel") == "visual_only":
                continue
            if fact.get("assigned_docs"):
                continue
            subject = fact["subject"] if fact["kind"] == "property" else fact["u"]
            homes = (self._docs_focused_on(subject, kinds=["wiki"])
                     or self._docs_focused_on(subject, kinds=["codex_entry"]))
            if homes:
                self.docs[homes[0]]["facts"].append(fid)
                fact["assigned_docs"] = [homes[0]]

    def _plan_atmo_images(self):
        """Atmospheric gpt-image-2 assets (carry no ground-truth numbers)."""
        specs = []
        for n in self._nodes("character", tier="major"):
            specs.append((n, "portrait"))
        for n in self._nodes("location"):
            if self.G.nodes[n].get("is_core"):
                specs.append((n, "landscape"))
        for n in self._nodes("faction"):
            specs.append((n, "heraldry"))
        for n in self._nodes("artifact"):
            specs.append((n, "relic"))
        for n in self._nodes("conflict"):
            specs.append((n, "battle_painting"))
        for n in self._nodes("creature"):
            specs.append((n, "creature"))
        for n, style in specs:
            image_id = f"atmo_{style}_{n}"
            host = self._docs_focused_on(n, kinds=["wiki"])
            spec = {
                "image_id": image_id, "entity": n, "entity_name": self._name(n),
                "style": style, "host_doc": host[0] if host else None,
                "filename": f"{image_id}.png",
            }
            # Controlled visual attribute (question-bearing if vision-verified).
            bank = VISUAL_ATTRIBUTE_BANK.get(style)
            if bank and host and self.rng.random() < 0.75:
                attr = self.rng.choice(bank)
                # Prefer answers not yet used for this slot, so no two factions
                # share an emblem and no two relics share a motif.
                used = getattr(self, "_used_attr_answers", None)
                if used is None:
                    used = self._used_attr_answers = {}
                taken = used.setdefault(attr["slot"], set())
                fresh = [o for o in attr["options"] if o not in taken]
                answer = self.rng.choice(fresh or attr["options"])
                taken.add(answer)
                spec["attribute"] = {
                    "slot": attr["slot"],
                    "answer": answer,
                    "detail": attr["detail"].format(x=answer),
                    "question": attr["question"].format(name=self._name(n)),
                }
            self.atmo_images[image_id] = spec
            if host:
                self.docs[host[0]]["images"].append(image_id)

    # ---------------------------------------------------------------- driver

    def _scrub_disputed_edge_attrs(self):
        """A disputed value must not leak through edge attributes.

        Example: if an artifact's 'forged' year is disputed, the FORGED_AT edge
        carries year=<true value> and would render '(in <year> AS)' in whatever
        document that edge lands in - bypassing the authority-tier isolation.
        Remove such attrs; the true value then exists only in the canon entry.
        """
        for d in self.disputes:
            for fact in self.facts.values():
                if fact["kind"] != "edge":
                    continue
                if d["entity"] not in (fact["u"], fact["v"]):
                    continue
                attrs = fact.get("attrs") or {}
                for key in ("year", "since"):
                    if attrs.get(key) == d["true_value"]:
                        del attrs[key]

    def plan(self) -> Dict[str, Any]:
        self._enumerate_facts()
        self._scrub_disputed_edge_attrs()
        self._select_visual_only()
        self._select_chains()
        self._plan_chronicles()
        self._plan_wiki()
        self._plan_codex()
        self._plan_ephemera()
        self._assign_facts()
        self._plan_atmo_images()
        return {
            "docs": self.docs,
            "facts": self.facts,
            "chains": self.chains,
            "visual_only": self.visual_only,
            "disputes": self.disputes,
            "figures": self.figures,
            "atmo_images": self.atmo_images,
            "scale": self.scale,
        }

    def validate(self) -> List[str]:
        """Returns a list of constraint violations (empty = plan is sound)."""
        problems = []
        doc_facts = {did: set(s["facts"]) for did, s in self.docs.items()}
        for ch in self.chains:
            for did, facts in doc_facts.items():
                if ch["edge1"] in facts and ch["edge2"] in facts:
                    problems.append(f"chain {ch['chain_id']} leaks in {did}")
        for fid in self.visual_only:
            for did, facts in doc_facts.items():
                if fid in facts:
                    problems.append(f"visual-only fact {fid} appears in text doc {did}")
        for d in self.disputes:
            fid = f"prop:{d['entity']}:{d['property']}"
            if fid in self.facts:
                for did in self.facts[fid].get("assigned_docs", []):
                    if self.docs[did]["tier"] != 1:
                        problems.append(f"disputed truth {fid} in non-canon doc {did}")
            for did in d.get("false_docs", []):
                if self.docs[did]["tier"] != 3:
                    problems.append(f"false claim {d['dispute_id']} in non-ephemera doc {did}")
        for fid, fact in self.facts.items():
            if fact.get("channel") == "visual_only":
                continue
            if not fact.get("assigned_docs"):
                problems.append(f"fact {fid} has no document")
        return problems
