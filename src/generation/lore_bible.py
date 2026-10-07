"""Lore bible: one canonical dossier per entity, written once, injected into
every later prompt so the novels, wiki, and codex all describe the same person
the same way (appearance, temperament, voice). Without this, each document
invents its own version of an entity and the corpus contradicts itself in ways
that are NOT ground-truthed - noise we cannot score.
"""
import asyncio
import json
import re
from typing import Dict, Any, List

import networkx as nx
from tqdm import tqdm

BIBLE_SYSTEM = (
    "You are the continuity editor of a grimdark fantasy franchise. You write short "
    "canonical dossiers that every author in the franchise must obey. Output pure JSON only."
)


def _fallback_dossier(node: Dict[str, Any]) -> Dict[str, str]:
    return {
        "dossier": f"{node['name']} is a {node['kind']} of the Ashen Era.",
        "appearance": "Undescribed; authors may keep descriptions minimal.",
        "demeanor": "Grim and guarded.",
    }


async def build_lore_bible(llm, G: nx.MultiDiGraph, batch_size: int = 8,
                           concurrency: int = 6,
                           exclude_props: Dict[str, set] = None) -> Dict[str, Dict[str, str]]:
    """exclude_props: {node_id: {prop, ...}} to withhold from the dossier prompt.

    Critical for benchmark validity: visual-only values (track 1A) and disputed
    values (track 1C) must NOT enter the dossiers, because dossiers are injected
    into every document prompt as canon - any number in them WILL end up in text.
    """
    exclude_props = exclude_props or {}
    nodes = list(G.nodes(data=True))
    batches: List[List] = [nodes[i:i + batch_size] for i in range(0, len(nodes), batch_size)]
    bible: Dict[str, Dict[str, str]] = {}
    sem = asyncio.Semaphore(concurrency)
    progress = tqdm(total=len(batches), desc="Dossier batches")

    async def do_batch(batch):
        listing = []
        for nid, d in batch:
            hidden = exclude_props.get(nid, set()) | {"kind", "name", "disputed_property"}
            props = {k: v for k, v in d.items() if k not in hidden}
            listing.append(f"- id: {nid} | kind: {d['kind']} | name: {d['name']} | facts: {json.dumps(props, default=str)}")
        prompt = (
            "Write a canonical dossier for each entity below in a grimdark fantasy world "
            "called the Ashen Era (a shattered feudal realm scarred by a magical cataclysm "
            "known as the Sundering; years are counted in 'AS').\n\n"
            + "\n".join(listing)
            + "\n\nFor EACH entity return: 'dossier' (2-3 sentences of canonical description "
            "grounded ONLY in the given facts - do not invent named entities, dates, or numbers), "
            "'appearance' (1 sentence: physical look / visual identity), "
            "'demeanor' (1 sentence: temperament or atmosphere).\n"
            "Output pure JSON: {\"<id>\": {\"dossier\": ..., \"appearance\": ..., \"demeanor\": ...}, ...}"
        )
        async with sem:
            try:
                for attempt in range(3):
                    try:
                        raw = await llm.generate_lore(prompt, system_prompt=BIBLE_SYSTEM, max_completion_tokens=4000)
                        match = re.search(r"\{.*\}", raw, re.DOTALL)
                        data = json.loads(match.group(0) if match else raw)
                        for nid, d in batch:
                            entry = data.get(nid)
                            bible[nid] = entry if isinstance(entry, dict) and "dossier" in entry else _fallback_dossier({"name": d["name"], "kind": d["kind"]})
                        return
                    except Exception as e:
                        if attempt == 2:
                            tqdm.write(f"[bible] batch failed after retries ({e}); using fallback dossiers")
                            for nid, d in batch:
                                bible[nid] = _fallback_dossier({"name": d["name"], "kind": d["kind"]})
                        else:
                            tqdm.write(f"[bible] batch attempt {attempt + 1} failed ({type(e).__name__}); retrying")
            finally:
                progress.update(1)

    await asyncio.gather(*(do_batch(b) for b in batches))
    progress.close()
    fallbacks = sum(1 for v in bible.values()
                    if v.get("appearance", "").startswith("Undescribed"))
    if fallbacks > len(bible) / 2:
        raise RuntimeError(
            f"Lore bible generation effectively failed: {fallbacks}/{len(bible)} entities "
            "got fallback stub dossiers. Check API credentials/deployments before continuing."
        )
    return bible
