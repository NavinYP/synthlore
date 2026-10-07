"""Long-form compilers for the competition corpus.

Key differences from the old DocumentCompiler:
- The LLM context is the PLANNER-ASSIGNED fact list, never the ego-graph, so
  fact placement constraints (visual-only, split chains, authority tiers)
  survive into the text.
- Chapters are generated in multiple continuation calls, so real 8-15 page
  chapters are possible despite per-call token limits.
- Every document is verified after generation: assigned facts must actually be
  expressed (entity names + values present). One retry with a mandatory-mention
  list; persistent misses are reported, not silently ignored.
"""
import asyncio
import re
from typing import Dict, Any, List, Tuple

import networkx as nx

from src.planning.corpus_planner import fact_to_text

WORLD_BLURB = (
    "The world: the Ashen Era, a shattered feudal realm two centuries after a magical "
    "cataclysm called the Sundering. Years are counted 'AS' (After the Sundering). "
    "Five powers contend over the ruins: the Ashen Vanguard, House Morvain, the Silent "
    "Choir, the Iron-Ring Cartel, and the Bleeding Crown."
)

COMMON_RULES = (
    "ABSOLUTE RULES:\n"
    "1. The GROUND TRUTH facts listed are canon. Express each of them clearly somewhere in the text, "
    "using the entities' exact names and exact numbers/years.\n"
    "2. NEVER assert a relationship, date, or number that is not in the provided facts. You may invent "
    "unnamed background color (weather, servants, meals) but NO new named entities, no new dates, no new statistics.\n"
    "3. No real-world references of any kind.\n"
    "4. Output Markdown only, no preamble or commentary about the task.\n"
)


def _base_name(name: str) -> str:
    """'Korvath Vane the Ashen' -> 'Korvath Vane' (for verification matching)."""
    return re.split(r" the ", name, maxsplit=1)[0].strip()


class CorpusCompiler:
    def __init__(self, llm, G: nx.MultiDiGraph, bible: Dict[str, Dict[str, str]], plan: Dict[str, Any]):
        self.llm = llm
        self.G = G
        self.bible = bible
        self.plan = plan
        self.facts = plan["facts"]

    # ------------------------------------------------------------- contexts

    def _fact_lines(self, spec: Dict[str, Any]) -> List[str]:
        return [fact_to_text(self.facts[fid], self.G) for fid in spec["facts"] if fid in self.facts]

    def _dossier_block(self, entity_ids: List[str], limit: int = 8) -> str:
        lines = []
        for nid in entity_ids[:limit]:
            if nid not in self.G.nodes:
                continue
            b = self.bible.get(nid, {})
            lines.append(f"- {self.G.nodes[nid]['name']} ({self.G.nodes[nid]['kind']}): "
                         f"{b.get('dossier', '')} Appearance: {b.get('appearance', '')} "
                         f"Demeanor: {b.get('demeanor', '')}")
        return "\n".join(lines)

    def _false_claim_block(self, spec: Dict[str, Any]) -> str:
        disputes = {d["dispute_id"]: d for d in self.plan["disputes"]}
        lines = []
        for did in spec.get("false_claims", []):
            d = disputes[did]
            lines.append(
                f"- Assert confidently, in this document's own voice, that {d['entity_name']}'s "
                f"{d['property']} year is {d['false_value']} AS. Do NOT hedge, do NOT mention the "
                f"claim is disputed, and do NOT state the value {d['true_value']}."
            )
        return "\n".join(lines)

    # -------------------------------------------------------------- chapter

    async def _compile_chapter(self, spec: Dict[str, Any]) -> str:
        pov = spec["pov"]
        pov_name = self.G.nodes[pov]["name"]
        fact_lines = self._fact_lines(spec)
        target = spec["target_words"]
        n_segments = max(2, round(target / 1600))
        per_segment = max(1, len(fact_lines) // n_segments + 1)

        system = (
            f"You are the author of a bestselling grimdark fantasy saga. {WORLD_BLURB}\n"
            "Write mature, atmospheric, literary prose: dialogue, interiority, sensory detail, "
            "political tension. Never summarize; dramatize.\n" + COMMON_RULES
        )

        segments: List[str] = []
        covered: List[str] = []
        for k in range(n_segments):
            batch = fact_lines[k * per_segment:(k + 1) * per_segment]
            covered_note = ("Facts ALREADY dramatized earlier in this chapter (do not restate, stay "
                            "consistent):\n" + "\n".join(f"- {f}" for f in covered)) if covered else ""
            tail = segments[-1][-700:] if segments else ""
            opening = (f"Begin the chapter titled '{spec['title']}' of the book '{spec['book']}'. "
                       f"Start with the Markdown heading '## {spec['title']}'."
                       if k == 0 else
                       "Continue the chapter seamlessly from the excerpt below. Do not repeat the "
                       f"excerpt, do not re-introduce the heading.\n\nPREVIOUS EXCERPT:\n...{tail}")
            prompt = (
                f"{opening}\n\n"
                f"POINT-OF-VIEW CHARACTER: {pov_name}\n\n"
                f"CANONICAL DOSSIERS:\n{self._dossier_block(spec['focus'] + [pov])}\n\n"
                f"GROUND TRUTH FACTS to dramatize in THIS section (each must appear explicitly, with "
                f"exact names and exact years/numbers):\n" + "\n".join(f"- {f}" for f in batch) + "\n\n"
                f"{covered_note}\n\n"
                f"Write approximately {target // n_segments} words of continuous scene prose. "
                + ("Bring the section to a natural cliffhanger or quiet close." if k == n_segments - 1
                   else "End mid-scene so the chapter can continue.")
            )
            text = await self.llm.generate_lore(prompt, system_prompt=system, max_completion_tokens=4000)
            segments.append(text.strip())
            covered.extend(batch)
        return "\n\n".join(segments)

    # ----------------------------------------------------------------- wiki

    async def _compile_wiki(self, spec: Dict[str, Any]) -> str:
        entity = spec["focus"][0]
        node = self.G.nodes[entity]
        fact_lines = self._fact_lines(spec)
        dispute_note = ""
        if spec.get("dispute_flags"):
            dispute_note = "DISPUTED FIELDS:\n" + "\n".join(f"- {f}" for f in spec["dispute_flags"]) + "\n\n"

        system = (
            f"You are the senior archivist of the official fan wiki for a grimdark fantasy franchise. {WORLD_BLURB}\n"
            "Write in encyclopedic wiki register.\n" + COMMON_RULES
        )
        prompt = (
            f"Write the complete wiki article for: {node['name']} ({node['kind']}).\n\n"
            f"CANONICAL DOSSIER:\n{self._dossier_block([entity])}\n\n"
            f"GROUND TRUTH FACTS (the article must state every one of these explicitly):\n"
            + "\n".join(f"- {f}" for f in fact_lines) + "\n\n"
            + dispute_note +
            "STRUCTURE:\n"
            "1. Open with a one-paragraph summary.\n"
            "2. An 'Infobox' as a two-column Markdown table (| Field | Value |) built ONLY from the facts above.\n"
            "3. Sections with ## headers: History, Relationships & Affiliations, and one thematic section "
            "of your choice (e.g. Legacy, Tactical Assessment, In Popular Memory).\n"
            "4. When mentioning another named entity, wrap its name in [[double brackets]].\n"
            f"5. Length: about {spec['target_words']} words.\n"
        )
        text = await self.llm.generate_lore(prompt, system_prompt=system, max_completion_tokens=4000)
        return self._attach_images(spec, text)

    def _attach_images(self, spec: Dict[str, Any], text: str) -> str:
        headers = []
        for image_id in spec.get("images", []):
            img = self.plan["atmo_images"][image_id]
            headers.append(f"![{img['entity_name']}](images/{img['filename']})")
        for figure_id in spec.get("figures", []):
            fig = self.plan["figures"][figure_id]
            headers.append(f"![Plate: {fig['entity_name']}](images/{fig['filename']})\n"
                           f"*Plate - {fig['entity_name']}: consult the plate for the recorded figures.*")
        if headers:
            return "\n\n".join(headers) + "\n\n" + text
        return text

    # ---------------------------------------------------------------- codex

    async def _compile_codex_entry(self, spec: Dict[str, Any]) -> str:
        entity = spec["focus"][0]
        node = self.G.nodes[entity]
        fact_lines = self._fact_lines(spec)
        canon_notes = ""
        if spec.get("canon_notes"):
            canon_notes = "AUTHORITATIVE CORRECTIONS (state these plainly and with full confidence):\n" \
                          + "\n".join(f"- {n}" for n in spec["canon_notes"]) + "\n\n"
        figure_note = ""
        if spec.get("figures"):
            figure_note = ("This entry is accompanied by a numbered plate. Refer the reader to the plate "
                           "for its recorded figures; do NOT state those numbers in the text.\n\n")

        system = (
            f"You are the compiler of an official lore codex (in the tradition of tabletop rulebooks). {WORLD_BLURB}\n"
            "Register: dry, clinical, authoritative. Prefer tables and terse annotations over prose.\n"
            + COMMON_RULES
        )
        prompt = (
            f"Write the codex entry '{spec['title']}' for the volume '{spec['book']}'.\n"
            f"Subject: {node['name']} ({node['kind']}).\n\n"
            f"CANONICAL DOSSIER:\n{self._dossier_block([entity])}\n\n"
            f"GROUND TRUTH FACTS (each must appear, exact names and numbers):\n"
            + "\n".join(f"- {f}" for f in fact_lines) + "\n\n"
            + canon_notes + figure_note +
            f"Include at least one Markdown table. Start with the header '### {spec['title']}'. "
            f"Length: about {spec['target_words']} words."
        )
        text = await self.llm.generate_lore(prompt, system_prompt=system, max_completion_tokens=2500)
        return self._attach_images(spec, text)

    # ------------------------------------------------------------- ephemera

    async def _compile_ephemera(self, spec: Dict[str, Any]) -> str:
        fact_lines = self._fact_lines(spec)
        false_block = self._false_claim_block(spec)
        focus_names = [self.G.nodes[n]["name"] for n in spec["focus"] if n in self.G.nodes]

        system = (
            f"You forge in-world ephemera for a grimdark fantasy franchise. {WORLD_BLURB}\n"
            "You write with the biased, limited, sometimes unreliable voice of a person inside the world.\n"
            + COMMON_RULES
        )
        prompt = (
            f"Write a {spec['ephemera_kind']} concerning {', '.join(focus_names)}.\n\n"
            f"CANONICAL DOSSIERS:\n{self._dossier_block(spec['focus'])}\n\n"
            + (("GROUND TRUTH FACTS to convey (exact names and numbers):\n"
                + "\n".join(f"- {f}" for f in fact_lines) + "\n\n") if fact_lines else "")
            + ((f"IN-CHARACTER CLAIMS this narrator sincerely believes (these override nothing; simply "
                f"present them as this narrator's stated belief):\n{false_block}\n\n") if false_block else "")
            + f"Match the medium's authentic form (salutations for letters, columns for ledgers, "
            f"verse for ballads, stage directions for transcripts). Length: about {spec['target_words']} words. "
            f"Start with a plausible in-world title line."
        )
        return await self.llm.generate_lore(prompt, system_prompt=system, max_completion_tokens=2000)

    # --------------------------------------------------------- verification

    def verify(self, spec: Dict[str, Any], text: str) -> List[str]:
        """Returns human-readable descriptions of assigned facts NOT expressed."""
        missing = []
        low = text.lower()
        for fid in spec["facts"]:
            fact = self.facts.get(fid)
            if not fact:
                continue
            if fact["kind"] == "property":
                name = _base_name(self.G.nodes[fact["subject"]]["name"]).lower()
                val = str(fact["value"]).lower()
                if len(val) > 30:
                    # Long prose values (doctrines, secrets, outcomes) are legitimately
                    # paraphrased; require the distinctive words rather than verbatim text.
                    words = [w for w in re.findall(r"[a-z][a-z'-]{4,}", val)]
                    hits = sum(1 for w in words if w in low)
                    ok = name in low and (not words or hits / len(words) >= 0.5)
                else:
                    ok = name in low and val in low
            else:
                ok = (_base_name(self.G.nodes[fact["u"]]["name"]).lower() in low
                      and _base_name(self.G.nodes[fact["v"]]["name"]).lower() in low)
            if not ok:
                missing.append(fact_to_text(fact, self.G))
        disputes = {d["dispute_id"]: d for d in self.plan["disputes"]}
        for did in spec.get("false_claims", []):
            d = disputes[did]
            if str(d["false_value"]) not in text:
                missing.append(f"[false claim] {d['false_claim']}")
        return missing

    async def compile_doc(self, spec: Dict[str, Any]) -> Tuple[str, List[str]]:
        dispatch = {
            "chapter": self._compile_chapter,
            "wiki": self._compile_wiki,
            "codex_entry": self._compile_codex_entry,
            "ephemera": self._compile_ephemera,
        }
        text = await dispatch[spec["kind"]](spec)
        missing = self.verify(spec, text)
        if missing:
            try:
                if spec["kind"] == "chapter":
                    # Chapters are too long to rewrite whole: append a closing scene
                    # that dramatizes the missed facts.
                    addendum = await self.llm.generate_lore(
                        "Continue the chapter below with one more closing scene of 300-500 words. "
                        "The scene MUST explicitly express each of these canonical facts (exact names, "
                        "exact numbers/years):\n" + "\n".join(f"- {m}" for m in missing)
                        + f"\n\nCHAPTER ENDING (for continuity):\n...{text[-800:]}",
                        system_prompt="You are the same grimdark fantasy author. Output scene prose in Markdown only.",
                        max_completion_tokens=2000,
                    )
                    text = text + "\n\n" + addendum.strip()
                else:
                    text = await self.llm.generate_lore(
                        "Below is a document from a grimdark fantasy corpus, followed by canonical facts it "
                        "was required to express but did not. Return the full document with the missing "
                        "facts woven in naturally (exact names, exact numbers). Do not remove existing content.\n\n"
                        f"DOCUMENT:\n{text}\n\nMISSING FACTS:\n" + "\n".join(f"- {m}" for m in missing),
                        system_prompt="You are a meticulous continuity editor. Output the corrected Markdown document only.",
                        max_completion_tokens=4000,
                    )
                missing = self.verify(spec, text)
            except Exception:
                pass
        return text, missing
