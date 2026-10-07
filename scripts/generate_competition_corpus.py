"""SyntheticLore-Bench - competition-grade corpus & benchmark generator.

Pipeline stages (each resumable; drafts and images are cached on disk):

  plan       Build the ground-truth world graph + the fact-placement plan.
  bible      Write canonical entity dossiers (LLM).
  text       Compile all documents from their assigned facts (LLM), verify.
  figures    Render programmatic fact plates (track 1A, no LLM).
  images     Generate atmospheric art via gpt-image-2.
  package    Assemble the distributable corpus: public/ vs answer_key/.
  benchmark  Build + verify the QA benchmark, split dev/eval.

Usage:
  python scripts/generate_competition_corpus.py --stages all
  python scripts/generate_competition_corpus.py --run_dir output/competition_xxx --stages text,package
  python scripts/generate_competition_corpus.py --stages all --volumes 2 --chapters 4 --ephemera 20   (small pilot)
"""
import argparse
import asyncio
import json
import os
import re
import shutil
import sys
import time
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import networkx as nx
from tqdm.asyncio import tqdm

from src.world.builder import WorldBuilder
from src.world.naming import slugify
from src.planning.corpus_planner import CorpusPlanner
from src.generation.llm_client import UnifiedAIClient
from src.generation.lore_bible import build_lore_bible
from src.generation.compilers import CorpusCompiler
from src.generation.fact_visuals import render_all_figures
from src.generation.atmo_visuals import generate_atmo_images
from src.generation import renderer_v2
from src.evaluation.benchmark import BenchmarkBuilder


def jdump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, default=str)


def jload(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state(run_dir):
    G = nx.node_link_graph(jload(os.path.join(run_dir, "answer_key", "world.json")),
                           edges="links", multigraph=True, directed=True)
    plan = jload(os.path.join(run_dir, "answer_key", "plan.json"))
    return G, plan


# ------------------------------------------------------------------ stages

# A deliberately tiny world for fast end-to-end pilots (~70 docs, ~80 LLM calls).
PILOT_COUNTS = {
    "major_characters": 6, "minor_characters": 6,
    "core_locations": 5, "minor_locations": 3,
    "artifacts": 4, "conflicts": 2, "creatures": 3, "disputes": 4,
}
PILOT_SCALE = {
    "volumes": 1, "chapters_per_volume": 3, "chapter_words": 2200,
    "wiki_words": 500, "codex_entry_words": 220,
    "ephemera_docs": 10, "ephemera_words": 250,
    "visual_only_facts": 6, "protected_chains": 8,
}


def stage_plan(run_dir, args):
    print("[plan] Building world graph and fact-placement plan...")
    builder = WorldBuilder(seed=args.seed, counts=PILOT_COUNTS if args.pilot else None)
    G = builder.build()
    if args.pilot:
        scale = dict(PILOT_SCALE)
    else:
        scale = {
            "volumes": args.volumes,
            "chapters_per_volume": args.chapters,
            "ephemera_docs": args.ephemera,
        }
    planner = CorpusPlanner(G, builder.disputes, seed=args.seed, scale=scale)
    plan = planner.plan()
    problems = planner.validate()
    if problems:
        raise RuntimeError("Plan constraint violations:\n" + "\n".join(problems[:20]))

    ak = os.path.join(run_dir, "answer_key")
    os.makedirs(ak, exist_ok=True)
    jdump(nx.node_link_data(G, edges="links"), os.path.join(ak, "world.json"))
    jdump(plan, os.path.join(ak, "plan.json"))
    summary = builder.summary()
    summary["documents"] = len(plan["docs"])
    summary["facts"] = len(plan["facts"])
    summary["protected_chains"] = len(plan["chains"])
    summary["visual_only_facts"] = len(plan["visual_only"])
    summary["figures"] = len(plan["figures"])
    summary["atmo_images"] = len(plan["atmo_images"])
    jdump(summary, os.path.join(ak, "plan_summary.json"))
    print(f"[plan] OK: {summary['documents']} docs, {summary['facts']} facts, "
          f"{summary['protected_chains']} chains, {summary['visual_only_facts']} visual-only, "
          f"0 violations.")


async def stage_bible(run_dir, args):
    G, plan = load_state(run_dir)
    path = os.path.join(run_dir, "answer_key", "lore_bible.json")
    if os.path.exists(path) and not args.force:
        print("[bible] Exists, skipping (use --force to regenerate).")
        return
    # Withhold visual-only and disputed values from the dossiers (leak vector).
    exclude = {}
    for fid in plan["visual_only"]:
        fact = plan["facts"][fid]
        exclude.setdefault(fact["subject"], set()).add(fact["prop"])
    for d in plan["disputes"]:
        exclude.setdefault(d["entity"], set()).add(d["property"])
    print(f"[bible] Writing canonical dossiers for {G.number_of_nodes()} entities "
          f"({len(exclude)} entities have withheld values)...")
    llm = UnifiedAIClient()
    await llm.preflight()
    try:
        bible = await build_lore_bible(llm, G, exclude_props=exclude)
    finally:
        await llm.close()
    jdump(bible, path)
    print(f"[bible] OK: {len(bible)} dossiers.")


async def stage_text(run_dir, args):
    G, plan = load_state(run_dir)
    bible = jload(os.path.join(run_dir, "answer_key", "lore_bible.json"))
    drafts_dir = os.path.join(run_dir, "drafts")
    os.makedirs(drafts_dir, exist_ok=True)

    llm = UnifiedAIClient()
    await llm.preflight()
    compiler = CorpusCompiler(llm, G, bible, plan)
    sem = asyncio.Semaphore(args.text_concurrency)
    report = {}

    async def one(doc_id, spec):
        out = os.path.join(drafts_dir, f"{doc_id}.md")
        if os.path.exists(out) and not args.force:
            return
        async with sem:
            try:
                text, missing = await compiler.compile_doc(spec)
                with open(out, "w", encoding="utf-8") as f:
                    f.write(text)
                if missing:
                    report[doc_id] = missing
            except Exception as e:
                report[doc_id] = [f"GENERATION FAILED: {e}"]
                tqdm.write(f"[text] {doc_id} FAILED: {type(e).__name__}: {e}")

    # Interleave slow chapters (3+ LLM calls each) with quick docs so early
    # completions surface fast and the semaphore isn't monopolized by chapters.
    chapters = [(d, s) for d, s in plan["docs"].items() if s["kind"] == "chapter"]
    others = [(d, s) for d, s in plan["docs"].items() if s["kind"] != "chapter"]
    ordered, ci, oi = [], 0, 0
    while ci < len(chapters) or oi < len(others):
        if ci < len(chapters):
            ordered.append(chapters[ci]); ci += 1
        for _ in range(max(1, len(others) // max(len(chapters), 1))):
            if oi < len(others):
                ordered.append(others[oi]); oi += 1

    tasks = [one(did, spec) for did, spec in ordered]
    print(f"[text] Compiling {len(tasks)} documents (concurrency {args.text_concurrency})...")
    for coro in tqdm.as_completed([asyncio.create_task(t) for t in tasks],
                                  total=len(tasks), desc="Compiling"):
        await coro
    await llm.close()

    jdump(report, os.path.join(run_dir, "answer_key", "verification_report.json"))
    done = len([f for f in os.listdir(drafts_dir) if f.endswith(".md")])
    print(f"[text] OK: {done}/{len(plan['docs'])} drafts; "
          f"{len(report)} docs with unresolved misses (see verification_report.json).")


def stage_figures(run_dir, args):
    _, plan = load_state(run_dir)
    out_dir = os.path.join(run_dir, "images")
    print(f"[figures] Rendering {len(plan['figures'])} fact plates...")
    render_all_figures(plan["figures"], out_dir)
    print("[figures] OK.")


async def stage_images(run_dir, args):
    _, plan = load_state(run_dir)
    if args.skip_images:
        print("[images] Skipped (--skip_images).")
        return
    out_dir = os.path.join(run_dir, "images")
    llm = UnifiedAIClient()
    await llm.preflight()
    print(f"[images] Generating {len(plan['atmo_images'])} atmospheric assets "
          f"(this is the slow stage, ~90s each at concurrency {args.image_concurrency})...")
    verif_path = os.path.join(run_dir, "answer_key", "atmo_verification.json")
    prior = jload(verif_path) if os.path.exists(verif_path) else {}
    try:
        status, verification = await generate_atmo_images(
            llm, plan["atmo_images"], out_dir,
            concurrency=args.image_concurrency, verification=prior)
    finally:
        await llm.close()
    failed = {k: v for k, v in status.items() if str(v).startswith("failed")}
    jdump(status, os.path.join(run_dir, "answer_key", "image_status.json"))
    jdump(verification, verif_path)
    n_ver = sum(1 for v in verification.values() if v.get("verified"))
    print(f"[images] OK: {len(status) - len(failed)} generated/cached, {len(failed)} failed; "
          f"visual attributes verified: {n_ver}/{len(verification)}.")


def stage_package(run_dir, args):
    G, plan = load_state(run_dir)
    drafts_dir = os.path.join(run_dir, "drafts")
    images_dir = os.path.join(run_dir, "images")
    public = os.path.join(run_dir, "public")
    if os.path.exists(public):
        shutil.rmtree(public)
    for sub in ["chronicles", "wiki", "wiki/images", "codex", "codex/images", "ephemera"]:
        os.makedirs(os.path.join(public, sub), exist_ok=True)

    doc_files = {}  # doc_id -> public-relative path

    def draft(doc_id):
        p = os.path.join(drafts_dir, f"{doc_id}.md")
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def copy_doc_images(spec, dest_subdir):
        for image_id in spec.get("images", []) + spec.get("figures", []):
            source = plan["atmo_images"].get(image_id) or plan["figures"].get(image_id)
            src = os.path.join(images_dir, source["filename"])
            if os.path.exists(src):
                shutil.copy2(src, os.path.join(public, dest_subdir, "images", source["filename"]))

    # --- Chronicles: one book per volume (PDF + DOCX).
    books = {}
    for doc_id, spec in plan["docs"].items():
        if spec["kind"] != "chapter":
            continue
        text = draft(doc_id)
        if text is None:
            continue
        books.setdefault(spec["book"], []).append((doc_id, spec["title"], text))
    for book, chapters in books.items():
        chapters.sort(key=lambda x: x[0])
        fname = slugify(book)
        pdf_rel = f"chronicles/{fname}.pdf"
        renderer_v2.render_pdf([(t, txt) for _, t, txt in chapters],
                               os.path.join(public, pdf_rel),
                               register="chronicle", title=book)
        renderer_v2.render_docx([(t, txt) for _, t, txt in chapters],
                                os.path.join(public, f"chronicles/{fname}.docx"), title=book)
        for doc_id, _, _ in chapters:
            doc_files[doc_id] = pdf_rel

    # --- Wiki: markdown files with images.
    for doc_id, spec in plan["docs"].items():
        if spec["kind"] != "wiki":
            continue
        text = draft(doc_id)
        if text is None:
            continue
        copy_doc_images(spec, "wiki")
        # Strip references to images that were not generated (e.g. --skip_images),
        # so distributed pages never carry broken links. Drafts keep the refs, so a
        # later images+package rerun restores the pictures.
        def keep_img(m):
            return m.group(0) if os.path.exists(
                os.path.join(public, "wiki", os.path.normpath(m.group(1)))) else ""
        text = re.sub(r"!\[[^\]]*\]\(([^)]+)\)\n?", keep_img, text)
        rel = f"wiki/{slugify(spec['title'])}.md"
        with open(os.path.join(public, rel), "w", encoding="utf-8") as f:
            f.write(text)
        doc_files[doc_id] = rel

    # --- Codex: one book per codex volume (PDF + DOCX), plates embedded.
    codex_books = {}
    for doc_id, spec in plan["docs"].items():
        if spec["kind"] != "codex_entry":
            continue
        text = draft(doc_id)
        if text is None:
            continue
        codex_books.setdefault(spec["book"], []).append((doc_id, spec["title"], text))
        copy_doc_images(spec, "codex")
    for book, entries in codex_books.items():
        entries.sort(key=lambda x: x[1])
        fname = slugify(book)
        pdf_rel = f"codex/{fname}.pdf"
        renderer_v2.render_pdf([(t, txt) for _, t, txt in entries],
                               os.path.join(public, pdf_rel),
                               register="codex", title=book,
                               image_root=os.path.join(public, "codex"))
        renderer_v2.render_docx([(t, txt) for _, t, txt in entries],
                                os.path.join(public, f"codex/{fname}.docx"), title=book,
                                image_root=os.path.join(public, "codex"))
        for doc_id, _, _ in entries:
            doc_files[doc_id] = pdf_rel

    # --- Ephemera: individual mixed-format files.
    for i, (doc_id, spec) in enumerate(sorted(plan["docs"].items())):
        if spec["kind"] != "ephemera":
            continue
        text = draft(doc_id)
        if text is None:
            continue
        fmt = spec["fmt"]
        rel = f"ephemera/{slugify(spec['title'])[:60]}{fmt}"
        renderer_v2.render_document(text, fmt, os.path.join(public, rel),
                                    title=spec["title"], register="ephemera", seed=i)
        doc_files[doc_id] = rel

    # A plain images/ folder at public root for benchmark evidence paths.
    os.makedirs(os.path.join(public, "images"), exist_ok=True)
    for fig in plan["figures"].values():
        src = os.path.join(images_dir, fig["filename"])
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(public, "images", fig["filename"]))

    with open(os.path.join(public, "README.txt"), "w", encoding="utf-8") as f:
        f.write(
            "SyntheticLore-Bench - Official Evaluation Document Corpus\n"
            "=========================================================\n\n"
            "An entirely fictional fantasy franchise archive ('the Ashen Era').\n\n"
            "  chronicles/  Narrative novels (PDF/DOCX), long chapters.\n"
            "  wiki/        Fan-wiki articles (Markdown) with images.\n"
            "  codex/       Official lore codexes and annals (PDF/DOCX) with plates.\n"
            "  ephemera/    In-world letters, ledgers, transcripts (mixed formats,\n"
            "               including scanned pages). WARNING: in-world authors are\n"
            "               not always reliable.\n"
            "  images/      Standalone figure plates.\n"
        )

    jdump(doc_files, os.path.join(run_dir, "answer_key", "doc_files.json"))
    n_files = sum(len(files) for _, _, files in os.walk(public))
    print(f"[package] OK: public corpus assembled ({n_files} files) -> {public}")


async def stage_benchmark(run_dir, args):
    G, plan = load_state(run_dir)
    doc_files = jload(os.path.join(run_dir, "answer_key", "doc_files.json"))
    drafts_dir = os.path.join(run_dir, "drafts")
    doc_texts = {}
    for f in os.listdir(drafts_dir):
        if f.endswith(".md"):
            with open(os.path.join(drafts_dir, f), "r", encoding="utf-8") as fh:
                doc_texts[f[:-3]] = fh.read()

    verif_path = os.path.join(run_dir, "answer_key", "atmo_verification.json")
    atmo_verification = jload(verif_path) if os.path.exists(verif_path) else {}

    llm = UnifiedAIClient()
    await llm.preflight()
    try:
        builder = BenchmarkBuilder(llm, G, plan, doc_texts, doc_files, seed=args.seed,
                                   atmo_verification=atmo_verification)
        print("[benchmark] Phrasing and verifying questions...")
        result = await builder.build(dev_ratio=args.dev_ratio,
                                     extra_chains=args.extra_chains,
                                     warmups=args.warmups)
    finally:
        await llm.close()

    ak = os.path.join(run_dir, "answer_key")
    jdump(result["dev"], os.path.join(ak, "benchmark_dev.json"))
    jdump(result["eval"], os.path.join(ak, "benchmark_eval.json"))
    jdump(result["rejected"], os.path.join(ak, "benchmark_rejected.json"))
    # Released file: dev questions only, no answers (answer release is still undecided).
    sample = [{"qid": x["qid"], "track": x["track"], "question": x["question"]}
              for x in result["dev"]]
    jdump(sample, os.path.join(run_dir, "public", "sample_questions.json"))
    print(f"[benchmark] OK: dev={len(result['dev'])}, eval={len(result['eval'])}, "
          f"rejected={len(result['rejected'])} (see benchmark_rejected.json).")


# ------------------------------------------------------------------- main

STAGES = ["plan", "bible", "text", "figures", "images", "package", "benchmark"]


async def run(args):
    if args.run_dir:
        run_dir = os.path.abspath(args.run_dir)
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        run_dir = os.path.join(base, "output",
                               f"competition_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    os.makedirs(run_dir, exist_ok=True)
    print(f"Run directory: {run_dir}")

    wanted = STAGES if args.stages == "all" else [s.strip() for s in args.stages.split(",")]
    for s in wanted:
        if s not in STAGES:
            raise SystemExit(f"Unknown stage '{s}'. Valid: {', '.join(STAGES)}")

    t0 = time.time()
    for s in STAGES:
        if s not in wanted:
            continue
        if s == "plan":
            stage_plan(run_dir, args)
        elif s == "bible":
            await stage_bible(run_dir, args)
        elif s == "text":
            await stage_text(run_dir, args)
        elif s == "figures":
            stage_figures(run_dir, args)
        elif s == "images":
            await stage_images(run_dir, args)
        elif s == "package":
            stage_package(run_dir, args)
        elif s == "benchmark":
            await stage_benchmark(run_dir, args)
    print(f"\nDone in {time.time() - t0:.1f}s. Run dir: {run_dir}")
    print("Distribute ONLY the public/ folder. answer_key/ stays with the judges.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Generate the official competition corpus.")
    p.add_argument("--stages", default="all", help=f"Comma list of: {', '.join(STAGES)} (or 'all')")
    p.add_argument("--run_dir", default=None, help="Existing run directory to resume")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--pilot", action="store_true",
                   help="Tiny world + short docs for a fast end-to-end test (~80 LLM calls)")
    p.add_argument("--volumes", type=int, default=4, help="Chronicle volumes")
    p.add_argument("--chapters", type=int, default=15, help="Chapters per volume")
    p.add_argument("--ephemera", type=int, default=150, help="Ephemera document count")
    p.add_argument("--dev_ratio", type=float, default=0.3, help="Share of questions released as dev set")
    p.add_argument("--extra_chains", type=int, default=0,
                   help="Optional: extra 1B chains mined from already-disjoint placements")
    p.add_argument("--warmups", type=int, default=0,
                   help="Optional: single-fact warm-up questions (released dev-only, not judged)")
    p.add_argument("--text_concurrency", type=int, default=8)
    p.add_argument("--image_concurrency", type=int, default=3)
    p.add_argument("--skip_images", action="store_true", help="Skip gpt-image-2 stage")
    p.add_argument("--force", action="store_true", help="Regenerate cached artifacts")
    args = p.parse_args()
    asyncio.run(run(args))
