"""Tests for the competition pipeline's validity-critical invariants.

These are the properties that make the benchmark defensible; a regression in
any of them silently invalidates a whole track.
"""
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from src.world.builder import WorldBuilder
from src.planning.corpus_planner import CorpusPlanner, fact_to_text


@pytest.fixture(scope="module")
def world():
    builder = WorldBuilder(seed=42)
    G = builder.build()
    return builder, G


@pytest.fixture(scope="module")
def planned(world):
    builder, G = world
    planner = CorpusPlanner(G, builder.disputes, seed=42,
                            scale={"volumes": 2, "chapters_per_volume": 4, "ephemera_docs": 30})
    plan = planner.plan()
    return planner, plan, G


def test_names_are_unique(world):
    _, G = world
    names = [d["name"] for _, d in G.nodes(data=True)]
    assert len(names) == len(set(names)), "duplicate entity names poison the ground truth"


def test_temporal_sanity(world):
    _, G = world
    for u, v, d in G.edges(data=True):
        if d.get("relation") == "FOUGHT_IN":
            assert G.nodes[v]["began"] >= G.nodes[u]["born"] + 16, \
                f"{G.nodes[u]['name']} fought before adulthood"
        if d.get("relation") == "WIELDS":
            assert d["since"] >= G.nodes[v]["forged"], \
                f"{G.nodes[v]['name']} wielded before it was forged"
    for n, d in G.nodes(data=True):
        if d.get("kind") == "character" and "died" in d:
            assert d["died"] > d["born"]


def test_slayings_are_consistent(world):
    _, G = world
    for u, v, d in G.edges(data=True):
        if d.get("relation") == "SLEW":
            assert G.nodes[v].get("died") == d["year"], "SLEW year must match victim's death"


def test_plan_has_no_violations(planned):
    planner, _, _ = planned
    assert planner.validate() == []


def test_chain_edges_never_cohabit(planned):
    _, plan, _ = planned
    assert len(plan["chains"]) > 0, "no protected chains selected"
    doc_facts = {did: set(s["facts"]) for did, s in plan["docs"].items()}
    for ch in plan["chains"]:
        for did, facts in doc_facts.items():
            assert not (ch["edge1"] in facts and ch["edge2"] in facts), \
                f"1B leak: chain {ch['chain_id']} fully contained in {did}"
        assert plan["facts"][ch["edge1"]]["assigned_docs"], "chain edge1 unplaced"
        assert plan["facts"][ch["edge2"]]["assigned_docs"], "chain edge2 unplaced"


def test_visual_only_facts_absent_from_text(planned):
    _, plan, _ = planned
    assert len(plan["visual_only"]) > 0
    for fid in plan["visual_only"]:
        for spec in plan["docs"].values():
            assert fid not in spec["facts"], f"1A leak: {fid} assigned to text"
        assert plan["facts"][fid].get("figure"), f"{fid} has no figure plate"


def test_dispute_authority_tiers(planned):
    _, plan, _ = planned
    assert len(plan["disputes"]) > 0
    for d in plan["disputes"]:
        assert plan["docs"][d["canon_doc"]]["tier"] == 1
        assert d["false_docs"], "false claim has no host document"
        for did in d["false_docs"]:
            assert plan["docs"][did]["tier"] == 3, "false claims must live in ephemera"
        assert d["canon_doc"] not in d["false_docs"]


def test_disputed_values_scrubbed_from_edge_attrs(planned):
    _, plan, _ = planned
    for d in plan["disputes"]:
        for fact in plan["facts"].values():
            if fact["kind"] != "edge" or d["entity"] not in (fact["u"], fact["v"]):
                continue
            attrs = fact.get("attrs") or {}
            for key in ("year", "since"):
                assert attrs.get(key) != d["true_value"], \
                    f"disputed value leaks via edge attr: {fact['fact_id']}"


def test_visual_attributes_well_formed(planned):
    from src.planning.corpus_planner import VISUAL_ATTRIBUTE_BANK
    _, plan, _ = planned
    with_attr = [s for s in plan["atmo_images"].values() if "attribute" in s]
    assert with_attr, "no atmo images received controlled attributes"
    for s in with_attr:
        a = s["attribute"]
        assert s["style"] in VISUAL_ATTRIBUTE_BANK
        assert a["answer"] in a["detail"], "detail must embed the answer phrase"
        assert s["entity_name"] in a["question"]
        assert s["host_doc"], "attribute images must have a host wiki page"


def test_every_fact_is_covered(planned):
    _, plan, _ = planned
    for fid, fact in plan["facts"].items():
        if fact.get("channel") == "visual_only":
            continue
        assert fact.get("assigned_docs"), f"orphan fact: {fid}"


def test_fact_rendering_readable(planned):
    _, plan, G = planned
    some = list(plan["facts"].values())[:20]
    for fact in some:
        line = fact_to_text(fact, G)
        assert "Unknown" not in line and len(line) > 5


def test_renderers_paginate(tmp_path):
    from src.generation import renderer_v2
    long_md = "# Title\n\n---\n\n" + ("Lorem grimdark ipsum dolor. " * 40 + "\n\n") * 60 \
              + "\n---\n\n| A | B |\n|---|---|\n| 1 | 2 |\n"
    pdf = tmp_path / "long.pdf"
    renderer_v2.render_pdf([("Chapter", long_md)], str(pdf), register="chronicle")
    assert pdf.stat().st_size > 10_000
    scan = tmp_path / "scan.pdf"
    renderer_v2.render_scanned_pdf(long_md, str(scan), seed=1)
    assert scan.stat().st_size > 50_000
    docx_p = tmp_path / "doc.docx"
    renderer_v2.render_docx([("Chapter", long_md)], str(docx_p))
    assert docx_p.stat().st_size > 5_000


def test_figure_plates_render(tmp_path, planned):
    from src.generation.fact_visuals import render_all_figures
    _, plan, _ = planned
    subset = dict(list(plan["figures"].items())[:3])
    render_all_figures(subset, str(tmp_path))
    for spec in subset.values():
        assert (tmp_path / spec["filename"]).exists()
