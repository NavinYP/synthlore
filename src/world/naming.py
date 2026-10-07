"""Combinatorial, collision-free name generation for the competition world.

Every name is drawn from curated banks and combined so that the pool is far
larger than the number of entities requested. A used-set guarantees global
uniqueness (the old pipeline produced duplicate conflict/artifact names, which
poisons the ground truth).
"""
import random
import re

FIRST_NAMES = [
    "Serathiel", "Korvath", "Maelis", "Draven", "Isolde", "Caedmon", "Vespera",
    "Alaric", "Nymeria", "Thaddric", "Elowen", "Gareth", "Sabelle", "Orin",
    "Lysandra", "Fenwick", "Morwenna", "Castellan", "Ravena", "Ossric",
    "Thessaly", "Brannoc", "Yvaine", "Corvus", "Adelheid", "Malchior",
    "Rhoswen", "Ederon", "Vionna", "Halvard", "Selwyn", "Tamsin", "Ignatz",
    "Merideth", "Aldous", "Cerys", "Voltaire", "Hesper", "Lucan", "Bryony",
]

SURNAMES = [
    "Vane", "Morvain", "Ashgrove", "Duskbane", "Hollowmere", "Crowhurst",
    "Veyra", "Blackspire", "Thornwald", "Greyfen", "Emberlyn", "Vosgard",
    "Palefroth", "Ironmere", "Sablewood", "Cindervale", "Wrenfield",
    "Oakhollow", "Marrowgate", "Stormwell", "Nightbrook", "Fellgard",
    "Ravensmoor", "Coldwater", "Harrowick", "Glassvane", "Mournvale",
]

EPITHETS = [
    "the Ashen", "the Unforgiven", "the Pale", "the Oathless", "the Silent",
    "the Red-Handed", "the Twice-Crowned", "the Hollow", "the Grave-Sworn",
    "the Lantern-Bearer", "the Flame-Touched", "the Last Warden",
]

LOC_PREFIX = [
    "Dusk", "Harrow", "Ember", "Vharen", "Mourn", "Grey", "Thorn", "Ash",
    "Raven", "Cinder", "Hollow", "Iron", "Sorrow", "Pale", "Black", "Storm",
    "Wither", "Gloam", "Bane", "Crook", "Fen", "Marrow", "Sable", "Wyrm",
]

LOC_SUFFIX = [
    "mere Hold", "spire", "gate Keep", "fell Citadel", "reach", "haven",
    "moor Bastion", "watch", "deep", "crag Fortress", "vale", "ford",
    "hollow Priory", "march", "throne", "cairn", "port", "well Abbey",
]

REGIONS = [
    "The Ash Wastes", "The Weeping Marshes", "The High Spires",
    "The Sunless Depths", "The Pale Coast", "The Blood-Moor",
    "The Gloaming Reach", "The Shattered Vale",
]

ARTIFACT_PATTERNS = [
    "The {adj} {noun}", "{noun} of {place_gen}", "The {noun} of {concept}",
]
ARTIFACT_ADJ = [
    "Weeping", "Sundered", "Hollow", "Grave-Cold", "Unsleeping", "Thrice-Bound",
    "Silent", "Cinder-Wrought", "Pale", "Oathbound", "Vengeful", "Moon-Dark",
]
ARTIFACT_NOUN = [
    "Edge", "Crown", "Chalice", "Lantern", "Psalter", "Aegis", "Diadem",
    "Reliquary", "Sceptre", "Mirror", "Gauntlet", "Bell", "Astrolabe", "Key",
]
CONCEPTS = [
    "Hollow Stars", "Final Winter", "Broken Vows", "Quiet Ruin",
    "Seven Sorrows", "Endless Vigil", "Burned Names", "Drowned Light",
]

CONFLICT_PATTERNS = [
    "The {adj} {noun}", "The {noun} of {place}", "The War of {concept}",
    "The {season} {noun}",
]
CONFLICT_ADJ = [
    "Crimson", "Sundering", "Faithless", "Winter", "Salt", "Burning",
    "Shrouded", "Kinslayer", "Leaden", "Starless",
]
CONFLICT_NOUN = [
    "Accord", "Reckoning", "Uprising", "Schism", "Siege", "Purge", "Mutiny",
    "Crusade", "Betrayal", "Interdict",
]
SEASONS = ["Long-Autumn", "Black-Spring", "Deep-Winter", "Ash-Summer"]

CREATURE_NAMES = [
    "Gravemaw Wyrm", "Cinder Shrike", "Hollow Sentinel", "Marsh Revenant",
    "Pale Stag of Omens", "Vault Chitin", "Weeping Lurker", "Ashfall Colossus",
    "Bone Choir", "Fen Hag", "Lantern Moth Swarm", "Spire Gargant",
    "Salt-Blind Leviathan", "Thorn Wraith", "Mourncall Raptor",
]


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


class NameForge:
    def __init__(self, rng: random.Random):
        self.rng = rng
        self.used = set()

    def _unique(self, maker, tries: int = 500) -> str:
        for _ in range(tries):
            name = maker()
            if name not in self.used:
                self.used.add(name)
                return name
        raise RuntimeError("Name banks exhausted; enlarge the banks or reduce entity counts.")

    def person(self, with_epithet: bool = False) -> str:
        def maker():
            base = f"{self.rng.choice(FIRST_NAMES)} {self.rng.choice(SURNAMES)}"
            if with_epithet and self.rng.random() < 0.6:
                base = f"{base} {self.rng.choice(EPITHETS)}"
            return base
        return self._unique(maker)

    def location(self) -> str:
        return self._unique(lambda: f"{self.rng.choice(LOC_PREFIX)}{self.rng.choice(LOC_SUFFIX)}")

    def artifact(self) -> str:
        def maker():
            pattern = self.rng.choice(ARTIFACT_PATTERNS)
            return pattern.format(
                adj=self.rng.choice(ARTIFACT_ADJ),
                noun=self.rng.choice(ARTIFACT_NOUN),
                place_gen=f"{self.rng.choice(LOC_PREFIX)}{self.rng.choice(LOC_SUFFIX)}".split(" ")[0],
                concept=self.rng.choice(CONCEPTS),
            )
        return self._unique(maker)

    def conflict(self) -> str:
        def maker():
            pattern = self.rng.choice(CONFLICT_PATTERNS)
            return pattern.format(
                adj=self.rng.choice(CONFLICT_ADJ),
                noun=self.rng.choice(CONFLICT_NOUN),
                place=f"{self.rng.choice(LOC_PREFIX)}{self.rng.choice(LOC_SUFFIX)}".split(" ")[0],
                concept=self.rng.choice(CONCEPTS),
                season=self.rng.choice(SEASONS),
            )
        return self._unique(maker)

    def creature(self) -> str:
        return self._unique(lambda: self.rng.choice(CREATURE_NAMES))

    def region(self) -> str:
        return self.rng.choice(REGIONS)
