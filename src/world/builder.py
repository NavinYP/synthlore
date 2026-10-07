"""WorldBuilder: constructs the competition ground-truth world.

Replaces the random-edge KnowledgeGraphGenerator for the competition corpus:
- Names are globally unique (NameForge).
- Each entity type has a coherent property schema (no "throughput" on castles).
- History is built as a timeline of conflicts with belligerents, sites,
  participants, and consequences, so edges follow narrative logic instead of
  uniform randomness.
- Temporal sanity is enforced (nobody fights in a war before they are born or
  after they die; artifacts are forged before they are wielded).
- Disputed facts (for the agentic track) are recorded explicitly with the true
  value, the false claim, and who spreads it - the planner routes them to
  documents of different authority tiers.

Years are given in the in-world calendar "AS" (After the Sundering).
"""
import random
import networkx as nx
from typing import Dict, Any, List, Optional

from src.world.naming import NameForge, slugify

ERA_START = 212
ERA_END = 468

FACTIONS = [
    {"name": "The Ashen Vanguard", "doctrine": "Militant order sworn to contain the Ley-ruins left by the Sundering.", "kind": "knightly order"},
    {"name": "House Morvain", "doctrine": "Ancient noble dynasty claiming descent from the last Sunder-Kings.", "kind": "noble house"},
    {"name": "The Silent Choir", "doctrine": "Secretive priesthood that records, censors, and rewrites history.", "kind": "priesthood"},
    {"name": "The Iron-Ring Cartel", "doctrine": "Mercantile league running contraband through the ruined trade roads.", "kind": "merchant cartel"},
    {"name": "The Bleeding Crown", "doctrine": "Royalist remnant fighting to restore the shattered monarchy.", "kind": "royalist remnant"},
]

CHARACTER_ROLES = [
    "High Inquisitor", "Blood-Mage", "Spymaster", "Arch-Prelate", "Sellsword Captain",
    "Master of Coin", "Warden-Commander", "Court Chronicler", "Reliquary Keeper",
    "Executioner", "Fleet Admiral", "Seneschal",
]

MINOR_ROLES = [
    "Quartermaster", "Scribe", "Outrider", "Gaoler", "Herbalist", "Toll-Reeve",
    "Lantern-Warden", "Falconer", "Sapper", "Choir Novice", "Smuggler", "Standard-Bearer",
]

ARTIFACT_CLASSES = ["blade", "regalia", "reliquary", "grimoire", "instrument", "ward"]

CONFLICT_OUTCOMES = [
    "ended in a brokered truce that satisfied no one",
    "ended with the total rout of the aggressors",
    "collapsed into a decade of guerrilla reprisals",
    "was decided by a betrayal at the eleventh hour",
    "ended when both hosts were destroyed by a Ley-storm",
    "was quietly settled by an exchange of hostages and relics",
]

CONFLICT_SECRETS = [
    "the spark that started it was staged by the Silent Choir",
    "the losing commander was bribed to withdraw",
    "the official chronicle halved the true casualty count",
    "a supposedly destroyed artifact was in fact spirited away",
    "the victors poisoned the wells of their own allies",
    "the war was prolonged deliberately to inflate Cartel profits",
]

CHARACTER_SECRETS = [
    "secretly practices proscribed blood-rites",
    "sells intelligence to the Iron-Ring Cartel",
    "forged their own lineage papers",
    "swore a hidden oath to the Silent Choir",
    "plotted the death of their own liege",
    "is the unacknowledged heir to the Bleeding Crown",
    "keeps a bound revenant in their cellar",
    "authored the heretical Palefroth Letters",
]

LOCATION_STATUS = ["garrisoned", "contested", "abandoned", "rebuilt", "quarantined"]


class WorldBuilder:
    def __init__(self, seed: int = 7, counts: Optional[Dict[str, int]] = None):
        self.rng = random.Random(seed)
        self.forge = NameForge(self.rng)
        self.graph = nx.MultiDiGraph()
        self.counts = {
            "major_characters": 12,
            "minor_characters": 40,
            "core_locations": 10,
            "minor_locations": 15,
            "artifacts": 12,
            "conflicts": 6,
            "creatures": 10,
            "disputes": 8,
        }
        if counts:
            self.counts.update(counts)
        self.disputes: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------ nodes

    def _add_node(self, kind: str, name: str, **props) -> str:
        node_id = f"{kind}_{slugify(name)}"
        self.graph.add_node(node_id, kind=kind, name=name, **props)
        return node_id

    def _nodes(self, kind: str) -> List[str]:
        return [n for n, d in self.graph.nodes(data=True) if d["kind"] == kind]

    def build(self) -> nx.MultiDiGraph:
        self._build_factions_and_locations()
        self._build_conflicts()
        self._build_characters()
        self._build_artifacts()
        self._build_creatures()
        self._build_participation()
        self._build_relationships()
        self._inject_disputes()
        return self.graph

    def _build_factions_and_locations(self):
        rng = self.rng
        self.faction_ids = []
        for f in FACTIONS:
            fid = self._add_node("faction", f["name"], doctrine=f["doctrine"], org_kind=f["kind"])
            self.faction_ids.append(fid)

        self.location_ids = []
        n_core = self.counts["core_locations"]
        for i in range(n_core + self.counts["minor_locations"]):
            name = self.forge.location()
            lid = self._add_node(
                "location", name,
                region=self.forge.region(),
                founded=rng.randint(ERA_START - 180, ERA_START + 120),
                garrison_strength=rng.randint(120, 9600),
                status=rng.choice(LOCATION_STATUS),
                is_core=(i < n_core),
            )
            self.location_ids.append(lid)

        # Each faction has a seat among the core locations, and rules it.
        core = [l for l in self.location_ids if self.graph.nodes[l]["is_core"]]
        seats = rng.sample(core, len(self.faction_ids))
        for fid, lid in zip(self.faction_ids, seats):
            self.graph.add_edge(fid, lid, relation="SEATED_AT")
            self.graph.add_edge(lid, fid, relation="RULED_BY")
        # Remaining locations get a ruling faction too.
        for lid in self.location_ids:
            if lid in seats:
                continue
            self.graph.add_edge(lid, rng.choice(self.faction_ids), relation="RULED_BY")

    def _build_conflicts(self):
        rng = self.rng
        self.conflict_ids = []
        n = self.counts["conflicts"]
        # Sequential, non-overlapping windows across the era.
        span = (ERA_END - ERA_START - 20) // n
        cursor = ERA_START + rng.randint(5, 15)
        for _ in range(n):
            began = cursor + rng.randint(0, max(1, span // 3))
            ended = began + rng.randint(2, max(3, span // 2))
            cursor = ended + rng.randint(3, 10)
            name = self.forge.conflict()
            cid = self._add_node(
                "conflict", name,
                began=began, ended=ended,
                casualty_figure=rng.randint(1200, 88000),
                outcome=rng.choice(CONFLICT_OUTCOMES),
                secret_truth=rng.choice(CONFLICT_SECRETS),
            )
            self.conflict_ids.append(cid)

            belligerents = rng.sample(self.faction_ids, rng.randint(2, 3))
            victor = rng.choice(belligerents)
            for fid in belligerents:
                self.graph.add_edge(fid, cid, relation="BELLIGERENT_IN")
            self.graph.add_edge(victor, cid, relation="VICTOR_OF")
            self.graph.nodes[cid]["victor"] = self.graph.nodes[victor]["name"]

            for lid in rng.sample(self.location_ids, rng.randint(2, 4)):
                rel = rng.choice(["WAGED_AT", "DEVASTATED"])
                self.graph.add_edge(cid, lid, relation=rel, year=rng.randint(began, ended))

    def _build_characters(self):
        rng = self.rng
        self.major_ids, self.minor_ids = [], []
        for i in range(self.counts["major_characters"]):
            name = self.forge.person(with_epithet=True)
            born = rng.randint(ERA_START + 20, ERA_END - 90)
            cid = self._add_node(
                "character", name,
                tier="major",
                role=CHARACTER_ROLES[i % len(CHARACTER_ROLES)],
                born=born,
                secret=rng.choice(CHARACTER_SECRETS),
            )
            self.major_ids.append(cid)
            faction = self.faction_ids[i % len(self.faction_ids)]
            self.graph.add_edge(cid, faction, relation="MEMBER_OF")
            # Majors command a location held by their faction when possible.
            faction_locs = [l for l in self.location_ids
                            if any(d.get("relation") == "RULED_BY" and v == faction
                                   for _, v, d in self.graph.out_edges(l, data=True))]
            target = rng.choice(faction_locs or self.location_ids)
            self.graph.add_edge(cid, target, relation="COMMANDS", since=born + rng.randint(20, 35))

        for i in range(self.counts["minor_characters"]):
            name = self.forge.person()
            born = rng.randint(ERA_START, ERA_END - 40)
            cid = self._add_node(
                "character", name,
                tier="minor",
                role=rng.choice(MINOR_ROLES),
                born=born,
            )
            self.minor_ids.append(cid)
            self.graph.add_edge(cid, rng.choice(self.faction_ids), relation="MEMBER_OF")
            # Minors serve at a location.
            self.graph.add_edge(cid, rng.choice(self.location_ids), relation="SERVES_AT")

    def _build_artifacts(self):
        rng = self.rng
        self.artifact_ids = []
        for _ in range(self.counts["artifacts"]):
            name = self.forge.artifact()
            forged = rng.randint(ERA_START - 150, ERA_END - 60)
            aid = self._add_node(
                "artifact", name,
                artifact_class=rng.choice(ARTIFACT_CLASSES),
                forged=forged,
                attunement_cost=rng.randint(3, 97),
            )
            self.artifact_ids.append(aid)
            self.graph.add_edge(aid, rng.choice(self.location_ids), relation="FORGED_AT", year=forged)
            self.graph.add_edge(aid, rng.choice(self.location_ids), relation="HOUSED_IN")
            # Wielder must be born and adult by a plausible wielding year.
            candidates = [c for c in self.major_ids
                          if self.graph.nodes[c]["born"] + 18 < ERA_END and self.graph.nodes[c]["born"] + 18 > forged - 200]
            wielder = rng.choice(candidates or self.major_ids)
            since = max(forged, self.graph.nodes[wielder]["born"] + 18) + rng.randint(0, 12)
            self.graph.add_edge(wielder, aid, relation="WIELDS", since=since)

    def _build_creatures(self):
        rng = self.rng
        self.creature_ids = []
        for _ in range(self.counts["creatures"]):
            name = self.forge.creature()
            cid = self._add_node(
                "creature", name,
                threat_rating=rng.randint(2, 10),
                habit=rng.choice(["nocturnal ambusher", "siege-breaker", "carrion swarm",
                                  "dream-feeder", "burrowing horror", "sky hunter"]),
            )
            self.creature_ids.append(cid)
            self.graph.add_edge(cid, rng.choice(self.location_ids), relation="LAIRS_IN")
            if rng.random() < 0.5:
                self.graph.add_edge(cid, rng.choice(self.conflict_ids), relation="UNLEASHED_IN")

    def _build_participation(self):
        """Characters fight in conflicts their faction waged, only while alive."""
        rng = self.rng
        faction_of = {}
        for c in self.major_ids + self.minor_ids:
            for _, v, d in self.graph.out_edges(c, data=True):
                if d.get("relation") == "MEMBER_OF":
                    faction_of[c] = v
        conflicts_of_faction = {f: [] for f in self.faction_ids}
        for f in self.faction_ids:
            for _, v, d in self.graph.out_edges(f, data=True):
                if d.get("relation") == "BELLIGERENT_IN":
                    conflicts_of_faction[f].append(v)

        for c in self.major_ids + self.minor_ids:
            born = self.graph.nodes[c]["born"]
            pool = [k for k in conflicts_of_faction.get(faction_of.get(c), [])
                    if self.graph.nodes[k]["began"] >= born + 16]
            is_major = self.graph.nodes[c]["tier"] == "major"
            take = min(len(pool), rng.randint(1, 3) if is_major else rng.randint(0, 1))
            for k in rng.sample(pool, take):
                self.graph.add_edge(c, k, relation="FOUGHT_IN",
                                    side=self.graph.nodes[faction_of[c]]["name"])

        # Some characters die in the last conflict they fought.
        for c in self.major_ids + self.minor_ids:
            fought = [v for _, v, d in self.graph.out_edges(c, data=True) if d.get("relation") == "FOUGHT_IN"]
            if fought and rng.random() < (0.35 if self.graph.nodes[c]["tier"] == "major" else 0.2):
                last = max(fought, key=lambda k: self.graph.nodes[k]["ended"])
                died = rng.randint(self.graph.nodes[last]["began"], self.graph.nodes[last]["ended"])
                self.graph.nodes[c]["died"] = died
                self.graph.nodes[c]["died_in"] = self.graph.nodes[last]["name"]

    def _build_relationships(self):
        rng = self.rng
        # Mentorships within a faction, respecting age gaps.
        for c in self.major_ids:
            juniors = [m for m in self.major_ids + self.minor_ids
                       if m != c and self.graph.nodes[m]["born"] > self.graph.nodes[c]["born"] + 18]
            if juniors and rng.random() < 0.6:
                self.graph.add_edge(c, rng.choice(juniors), relation="MENTOR_OF")

        # Rivalries between majors of opposing factions who shared a conflict.
        shared = {}
        for c in self.major_ids:
            shared[c] = {v for _, v, d in self.graph.out_edges(c, data=True) if d.get("relation") == "FOUGHT_IN"}
        pairs = []
        for i, a in enumerate(self.major_ids):
            for b in self.major_ids[i + 1:]:
                common = shared[a] & shared[b]
                if common:
                    pairs.append((a, b, next(iter(common))))
        rng.shuffle(pairs)
        for a, b, k in pairs[:6]:
            self.graph.add_edge(a, b, relation="RIVAL_OF")
            self.graph.add_edge(b, a, relation="RIVAL_OF")
            # A rivalry may end in a killing consistent with recorded deaths.
            victim, killer = (a, b) if "died" in self.graph.nodes[a] else (b, a)
            if "died" in self.graph.nodes[victim] and "died" not in self.graph.nodes[killer] and rng.random() < 0.6:
                self.graph.add_edge(killer, victim, relation="SLEW",
                                    year=self.graph.nodes[victim]["died"],
                                    during=self.graph.nodes[victim].get("died_in", ""))

    # -------------------------------------------------------------- disputes

    def _inject_disputes(self):
        """Pick facts that will be contested by unreliable sources.

        The TRUE value stays on the node. The FALSE claim is recorded here and
        the planner routes it exclusively to low-authority documents, while the
        true value is guaranteed a home in a canonical (tier-1) document.
        """
        rng = self.rng
        candidates = []
        for lid in self.location_ids:
            candidates.append((lid, "founded"))
        for c in self.major_ids:
            if "died" in self.graph.nodes[c]:
                candidates.append((c, "died"))
        for aid in self.artifact_ids:
            candidates.append((aid, "forged"))
        rng.shuffle(candidates)

        spreaders = ["a tavern ballad", "a discredited chronicler", "Cartel broadsheets",
                     "a heretical pamphlet", "the enemy's court records", "a forged charter"]
        for node_id, prop in candidates[: self.counts["disputes"]]:
            true_val = self.graph.nodes[node_id][prop]
            false_val = true_val + rng.choice([-31, -17, -9, 12, 23, 40])
            self.disputes.append({
                "dispute_id": f"dispute_{node_id}_{prop}",
                "entity": node_id,
                "entity_name": self.graph.nodes[node_id]["name"],
                "property": prop,
                "true_value": true_val,
                "false_value": false_val,
                "spreader": rng.choice(spreaders),
                "false_claim": (
                    f"According to {rng.choice(spreaders)}, {self.graph.nodes[node_id]['name']} "
                    f"{'fell' if prop == 'died' else ('was forged' if prop == 'forged' else 'was founded')} "
                    f"in {false_val} AS."
                ),
            })
            self.graph.nodes[node_id]["disputed_property"] = prop

    # ------------------------------------------------------------------ misc

    def summary(self) -> Dict[str, Any]:
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "era": f"{ERA_START}-{ERA_END} AS",
            "disputes": len(self.disputes),
            "by_kind": {k: len(self._nodes(k)) for k in
                        ["faction", "character", "location", "artifact", "conflict", "creature"]},
        }
