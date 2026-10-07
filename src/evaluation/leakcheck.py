"""Shared leak detection for benchmark answers.

A value 'leaks' into text only if it appears NEAR a mention of its entity.
Document-wide co-occurrence is far too blunt at corpus scale: single-digit
threat ratings match digits inside comma-grouped numbers ("9,478"), and one
entity's year legitimately appearing in a chapter (Cindermere Hold, founded
246 AS) must not count as a leak for a different entity (Gloamreach) that
merely shares the chapter and the year.
"""
import re
from typing import List, Optional

WINDOW = 200  # characters; roughly two sentences


def leak_near(text: str, entity_base: str, value, window: int = WINDOW,
              rival_names: Optional[List[str]] = None) -> bool:
    """True if `value` occurs within `window` chars of an `entity_base` mention
    AND is best attributed to that entity.

    Comma grouping is stripped before matching so "9,478" cannot produce a
    phantom standalone "9". If `rival_names` is given (other entities that
    legitimately carry the same value), an occurrence is not counted when a
    rival is mentioned closer to the number than the entity under test - e.g.
    "Cindermere Hold, founded in 246 AS" in a scene that also names Gloamreach
    attributes 246 to Cindermere, not Gloamreach.
    """
    hay = text.lower().replace(",", "")
    ent = entity_base.lower().replace(",", "")
    val = str(value).lower().replace(",", "")
    ent_pos = [m.start() for m in re.finditer(re.escape(ent), hay)]
    if not ent_pos:
        return False
    rival_pos = []
    for r in rival_names or []:
        r = r.lower().replace(",", "")
        if r and r != ent:
            rival_pos += [m.start() for m in re.finditer(re.escape(r), hay)]
    for m in re.finditer(rf"\b{re.escape(val)}\b", hay):
        p = m.start()
        d_ent = min(abs(p - e) for e in ent_pos)
        if d_ent > window:
            continue
        d_rival = min((abs(p - r) for r in rival_pos), default=None)
        if d_rival is not None and d_rival < d_ent:
            continue  # the number belongs to the rival's mention
        return True
    return False


def value_owners(G, value, exclude_node=None) -> List[str]:
    """Base names of entities whose own properties carry this exact value."""
    owners = []
    for nid, d in G.nodes(data=True):
        if nid == exclude_node:
            continue
        if any(v == value for k, v in d.items() if isinstance(v, int)):
            owners.append(re.split(r" the ", d["name"], maxsplit=1)[0])
    return owners
