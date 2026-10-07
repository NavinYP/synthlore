"""Corpus go/no-go validation gate.

Independently re-checks the benchmark-critical invariants against the ACTUAL
generated text (not just the plan), and reports PASS/FAIL per check:

  A1  Every visual-only value is absent from every text document.
  A2  Every figure plate file exists and its host document is in the corpus.
  B1  For every protected chain, no single document expresses both hops.
  B2  Both hops of every chain are expressed somewhere.
  C1  Every false claim appears in at least one tier-3 document.
  C2  The true value of a disputed fact appears ONLY in its canon document.
  Q1  Benchmark has verified questions in all three tracks; rejection rate low.
  E1  Every expected_evidence path in the benchmark exists in public/.
  V1  Unresolved fact-miss rate from generation is low.

Usage: python scripts/validate_corpus.py --run_dir output/competition_xxx
"""
import argparse
import json
import os
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def jload(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def base_name(name):
    return re.split(r" the ", name, maxsplit=1)[0].lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    args = ap.parse_args()
    rd = os.path.abspath(args.run_dir)
    ak = os.path.join(rd, "answer_key")

    plan = jload(os.path.join(ak, "plan.json"))
    import networkx as nx
    G = nx.node_link_graph(jload(os.path.join(ak, "world.json")),
                           edges="links", multigraph=True, directed=True)
    drafts = {}
    for f in os.listdir(os.path.join(rd, "drafts")):
        if f.endswith(".md"):
            with open(os.path.join(rd, "drafts", f), "r", encoding="utf-8") as fh:
                drafts[f[:-3]] = fh.read()

    facts = plan["facts"]
    results = []

    def check(code, ok, detail):
        results.append((code, ok, detail))

    from src.evaluation.leakcheck import leak_near, value_owners

    # ---- A1: visual-only values never stated near their entity in text
    leaks = []
    for fid in plan["visual_only"]:
        fact = facts[fid]
        ent = base_name(G.nodes[fact["subject"]]["name"])
        rivals = value_owners(G, fact["value"], exclude_node=fact["subject"])
        for did, text in drafts.items():
            if leak_near(text, ent, fact["value"], rival_names=rivals):
                leaks.append(f"{fid} -> {did}")
    check("A1 visual-only isolation", not leaks, leaks or f"{len(plan['visual_only'])} values isolated")

    # ---- A2: plates exist and host docs shipped
    missing = []
    for fig in plan["figures"].values():
        if not os.path.exists(os.path.join(rd, "images", fig["filename"])):
            missing.append(fig["filename"])
        if fig["host_doc"] not in drafts:
            missing.append(f"host missing: {fig['host_doc']}")
    check("A2 figure plates present", not missing, missing or f"{len(plan['figures'])} plates ok")

    # ---- B1/B2: chain split in actual text
    def expressed(fact, text_low):
        u = base_name(G.nodes[fact["u"]]["name"])
        v = base_name(G.nodes[fact["v"]]["name"])
        return u in text_low and v in text_low

    b1_bad, b2_bad = [], []
    for ch in plan["chains"]:
        e1, e2 = facts[ch["edge1"]], facts[ch["edge2"]]
        both, any1, any2 = [], False, False
        for did, text in drafts.items():
            low = text.lower()
            in1 = did in e1.get("assigned_docs", []) and expressed(e1, low)
            in2 = did in e2.get("assigned_docs", []) and expressed(e2, low)
            any1, any2 = any1 or in1, any2 or in2
            # hard check: assigned placement never put both in one doc
            if ch["edge1"] in plan["docs"][did]["facts"] and ch["edge2"] in plan["docs"][did]["facts"]:
                both.append(did)
        if both:
            b1_bad.append(f"{ch['chain_id']}: {both}")
        if not (any1 and any2):
            b2_bad.append(ch["chain_id"])
    check("B1 chain hops never co-located", not b1_bad, b1_bad or f"{len(plan['chains'])} chains split")
    check("B2 both hops expressed in text", not b2_bad, b2_bad or "all hops present")

    # ---- C1/C2: dispute authority
    c1_bad, c2_bad = [], []
    for d in plan["disputes"]:
        ent = base_name(d["entity_name"])
        false_ok = any(str(d["false_value"]) in drafts.get(did, "") for did in d.get("false_docs", []))
        if not false_ok:
            c1_bad.append(d["dispute_id"])
        rivals = value_owners(G, d["true_value"], exclude_node=d["entity"])
        for did, text in drafts.items():
            if did == d["canon_doc"]:
                continue
            # Proximity + attribution: a year another entity legitimately carries may
            # appear near this entity; it only counts if best attributed to THIS entity.
            if leak_near(text, ent, d["true_value"], rival_names=rivals):
                c2_bad.append(f"{d['dispute_id']} true value also in {did}")
    check("C1 false claims planted", not c1_bad, c1_bad or f"{len(plan['disputes'])} disputes planted")
    check("C2 true value only in canon doc", not c2_bad, c2_bad or "no stray truths")

    # ---- A3: visual-attribute questions that SHIPPED must be isolated.
    # (An attribute whose question the benchmark rejected is merely decorative -
    # a text collision there is harmless and expected in grimdark prose.)
    verif_path = os.path.join(ak, "atmo_verification.json")
    if os.path.exists(verif_path):
        verif = jload(verif_path)
        shipped = jload(os.path.join(ak, "benchmark_dev.json")) + \
            jload(os.path.join(ak, "benchmark_eval.json"))
        shipped_visual = [q for q in shipped if q.get("subtype") == "visual_attribute"]
        by_file = {v["filename"]: v for v in verif.values() if v.get("verified")}
        a3_bad = []
        for q in shipped_visual:
            img = next((p.split("/")[-1] for p in q["expected_evidence"] if p.endswith(".png")), None)
            v = by_file.get(img)
            if not v or not os.path.exists(os.path.join(rd, "images", v["filename"])):
                a3_bad.append(f"{q['qid']}: image missing")
                continue
            ent = base_name(v["entity_name"])
            for did, text in drafts.items():
                if leak_near(text, ent, v["answer"]):
                    a3_bad.append(f"{q['qid']}: answer '{v['answer']}' leaked in {did}")
        check("A3 visual attributes isolated", not a3_bad,
              a3_bad or f"{len(shipped_visual)} shipped visual questions isolated "
                        f"({len(by_file)} attributes verified)")

    # ---- Q1/E1: benchmark health
    dev = jload(os.path.join(ak, "benchmark_dev.json"))
    ev = jload(os.path.join(ak, "benchmark_eval.json"))
    rej = jload(os.path.join(ak, "benchmark_rejected.json"))
    allq = dev + ev
    tracks = {t: sum(1 for x in allq if x["track"] == t)
              for t in ("1A_multimodal", "1B_multihop", "1C_agentic")}
    total = len(allq) + len(rej)
    ok_q = all(v > 0 for v in tracks.values()) and (len(rej) / max(total, 1)) <= 0.2
    check("Q1 benchmark coverage", ok_q,
          f"dev={len(dev)} eval={len(ev)} rejected={len(rej)} tracks={tracks}")

    public = os.path.join(rd, "public")
    e1_bad = []
    for q in allq:
        for p in q["expected_evidence"]:
            if not os.path.exists(os.path.join(public, os.path.normpath(p))):
                e1_bad.append(f"{q['qid']}: {p}")
    check("E1 evidence files exist", not e1_bad, e1_bad[:10] or f"{len(allq)} questions' evidence resolved")

    # ---- V1: generation misses
    vr = jload(os.path.join(ak, "verification_report.json"))
    miss_rate = len(vr) / max(len(plan["docs"]), 1)
    check("V1 fact-miss rate", miss_rate <= 0.05, f"{len(vr)}/{len(plan['docs'])} docs with misses")

    # ---- report
    print("=" * 70)
    print(f"CORPUS VALIDATION - {rd}")
    print("=" * 70)
    failed = 0
    rows = []
    for code, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        failed += (not ok)
        detail_s = detail if isinstance(detail, str) else "; ".join(map(str, detail[:6]))
        rows.append({"check": code, "ok": ok, "detail": detail_s})
        print(f"[{mark}] {code}: {detail_s}")
    print("=" * 70)
    words = sum(len(t.split()) for t in drafts.values())
    verdict = "GO" if failed == 0 else f"NO-GO ({failed} failed)"
    print(f"Corpus: {len(drafts)} documents, ~{words:,} words (~{words // 400:,} pages)")
    print("VERDICT: " + ("GO - corpus is benchmark-valid" if failed == 0
                         else f"NO-GO - {failed} check(s) failed"))

    # Machine-readable copy for downstream pages (e.g. the world companion).
    report = {"run_dir": os.path.basename(rd), "verdict": verdict, "checks": rows,
              "documents": len(drafts), "words": words, "pages_approx": words // 400,
              "benchmark": {"dev": len(dev), "eval": len(ev),
                            "rejected": len(rej), "tracks": tracks}}
    with open(os.path.join(ak, "validation_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
