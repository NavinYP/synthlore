"""Builds the organizer-facing 'Ashen Era companion' web page from a run.

One self-contained HTML file: world overview, faction dossiers, conflict
timeline, major-character gallery, relics & bestiary, the judges-only hidden
layer (secrets and disputes), and the interactive knowledge-graph atlas.
Generated images are embedded as small JPEG thumbnails when present; rerun the
script after the images stage completes to pick them up.

Usage:
  python scripts/build_world_companion.py --run_dir output/competition_xxx [--out share/ashen_era_companion.html]
"""
import argparse
import base64
import html
import io
import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"]


def esc(s):
    return html.escape(str(s), quote=True)


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def thumb_data_uri(path, width=420, quality=70):
    try:
        from PIL import Image
        img = Image.open(path).convert("RGB")
        img.thumbnail((width, width))
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=quality)
        return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return None


class World:
    def __init__(self, run_dir, assets_mode="embed", assets_out=None):
        self.run_dir = run_dir
        data = jload(os.path.join(run_dir, "answer_key", "world.json"))
        self.nodes = {n["id"]: n for n in data["nodes"]}
        self.links = data["links"]
        self.bible = jload(os.path.join(run_dir, "answer_key", "lore_bible.json"))
        self.plan = jload(os.path.join(run_dir, "answer_key", "plan.json"))
        self.img_dir = os.path.join(run_dir, "images")
        vr = os.path.join(run_dir, "answer_key", "validation_report.json")
        self.validation = jload(vr) if os.path.exists(vr) else None
        self.assets_mode = assets_mode  # "embed" = data URIs; "files" = images/ folder
        self.assets_out = assets_out

    def out_edges(self, nid, rel=None):
        return [(l["target"], l["relation"]) for l in self.links
                if l["source"] == nid and (rel is None or l["relation"] == rel)]

    def in_edges(self, nid, rel=None):
        return [(l["source"], l["relation"]) for l in self.links
                if l["target"] == nid and (rel is None or l["relation"] == rel)]

    def name(self, nid):
        return self.nodes[nid]["name"]

    def by_kind(self, kind, **filters):
        out = []
        for nid, n in self.nodes.items():
            if n["kind"] != kind:
                continue
            if all(n.get(k) == v for k, v in filters.items()):
                out.append(nid)
        return out

    def dossier(self, nid):
        return self.bible.get(nid, {})

    def image(self, style, nid):
        p = os.path.join(self.img_dir, f"atmo_{style}_{nid}.png")
        if not os.path.exists(p):
            return None
        if self.assets_mode == "files":
            # Larger thumbs are fine when they live as separate files.
            fname = f"atmo_{style}_{nid}.jpg"
            dest = os.path.join(self.assets_out, fname)
            if not os.path.exists(dest):
                try:
                    from PIL import Image
                    img = Image.open(p).convert("RGB")
                    img.thumbnail((720, 720))
                    img.save(dest, "JPEG", quality=78)
                except Exception:
                    return None
            return f"images/{fname}"
        return thumb_data_uri(p)


def img_or_placeholder(uri, alt, cls="thumb"):
    if uri:
        return f'<img class="{cls}" src="{uri}" alt="{esc(alt)}" loading="lazy">'
    return f'<div class="{cls} placeholder">art<br>pending</div>'


def render_overview(w):
    plan = w.plan
    kinds = {}
    for spec in plan["docs"].values():
        kinds[spec["kind"]] = kinds.get(spec["kind"], 0) + 1
    n_chars = len(w.by_kind("character"))
    return f"""
<h2>The world in one page</h2>
<p class="lede">Two centuries ago a magical cataclysm called <strong>the Sundering</strong> shattered
a continent-spanning empire. Years are counted <strong>AS</strong> (After the Sundering), and the era
this corpus covers runs roughly <strong>212 to 468 AS</strong>. Five powers contend over the ruins and
the failing Ley-relics beneath them. The corpus is that world's paper trail: its novels, its fan wiki,
its official codexes, and the letters and ledgers of the people living in it.</p>
<div class="statgrid">
  <div><b>{n_chars}</b><span>characters ({len(w.by_kind("character", tier="major"))} major)</span></div>
  <div><b>{len(w.by_kind("location"))}</b><span>locations</span></div>
  <div><b>{len(w.by_kind("conflict"))}</b><span>wars &amp; crises</span></div>
  <div><b>{len(w.by_kind("artifact"))}</b><span>artifacts</span></div>
  <div><b>{len(w.by_kind("creature"))}</b><span>creatures</span></div>
  <div><b>{len(w.by_kind("faction"))}</b><span>factions</span></div>
</div>
<h3>How the world becomes documents</h3>
<p>Every fact lives in one ground-truth graph. A planner then assigns each fact to specific documents:
{kinds.get("chapter", 0)} novel chapters carry the narrative, {kinds.get("wiki", 0)} wiki articles
summarize entities, {kinds.get("codex_entry", 0)} codex entries hold the dry canonical data, and
{kinds.get("ephemera", 0)} pieces of ephemera add in-world voices that are not always honest.
Three special channels exist for the competition: numeric facts that appear <em>only</em> in figure
plates, two-hop fact chains split so no single document contains both hops, and disputed facts whose
truth lives only in the codex while confident lies circulate in ephemera.</p>
"""


def render_factions(w):
    cards = []
    for fid in w.by_kind("faction"):
        n = w.nodes[fid]
        d = w.dossier(fid)
        seat = [w.name(t) for t, _ in w.out_edges(fid, "SEATED_AT")]
        members = [s for s, _ in w.in_edges(fid, "MEMBER_OF")]
        majors = [w.name(m) for m in members if w.nodes[m].get("tier") == "major"]
        wars = [w.name(t) for t, _ in w.out_edges(fid, "BELLIGERENT_IN")]
        won = [w.name(t) for t, _ in w.out_edges(fid, "VICTOR_OF")]
        uri = w.image("heraldry", fid)
        cards.append(f"""
<article class="card">
  {img_or_placeholder(uri, "Banner of " + n["name"])}
  <div class="cardbody">
    <h3>{esc(n["name"])}</h3>
    <p class="tag">{esc(n.get("org_kind", ""))} · seat: {esc(", ".join(seat) or "none")}</p>
    <p>{esc(n.get("doctrine", ""))}</p>
    <p class="dossier">{esc(d.get("dossier", ""))}</p>
    <p class="meta">{len(members)} sworn members · notable: {esc(", ".join(majors) or "none")}<br>
    wars: {esc(", ".join(wars) or "none")}{(" · victories: " + esc(", ".join(won))) if won else ""}</p>
  </div>
</article>""")
    return "<h2>The five powers</h2>\n" + "\n".join(cards)


def render_conflicts(w):
    rows = []
    conflicts = sorted(w.by_kind("conflict"), key=lambda c: w.nodes[c]["began"])
    for i, cid in enumerate(conflicts):
        n = w.nodes[cid]
        d = w.dossier(cid)
        bell = [w.name(s) for s, _ in w.in_edges(cid, "BELLIGERENT_IN")]
        sites = [w.name(t) for t, r in w.out_edges(cid) if r in ("WAGED_AT", "DEVASTATED")]
        fighters = [w.name(s) for s, _ in w.in_edges(cid, "FOUGHT_IN")
                    if w.nodes[s].get("tier") == "major"]
        uri = w.image("battle_painting", cid)
        rows.append(f"""
<article class="card wide">
  {img_or_placeholder(uri, n["name"])}
  <div class="cardbody">
    <p class="tag">{esc(n["began"])} - {esc(n["ended"])} AS</p>
    <h3>{esc(n["name"])}</h3>
    <p class="dossier">{esc(d.get("dossier", ""))}</p>
    <p class="meta">belligerents: {esc(" vs ".join(bell))} · victor: <strong>{esc(n.get("victor", "?"))}</strong><br>
    fought over: {esc(", ".join(sorted(set(sites))))}<br>
    notable combatants: {esc(", ".join(sorted(set(fighters))) or "chronicled in the volumes")}</p>
    <p class="meta">outcome: {esc(n.get("outcome", ""))}</p>
  </div>
</article>""")
    return ("<h2>The chronicle of the era</h2>"
            "<p class='lede'>Six conflicts structure the timeline; the novels dramatize them, "
            "the Annals record them, and the ephemera argue about them.</p>\n" + "\n".join(rows))


def render_characters(w):
    cards = []
    majors = sorted(w.by_kind("character", tier="major"), key=lambda c: w.nodes[c]["born"])
    for cid in majors:
        n = w.nodes[cid]
        d = w.dossier(cid)
        faction = [w.name(t) for t, _ in w.out_edges(cid, "MEMBER_OF")]
        commands = [w.name(t) for t, _ in w.out_edges(cid, "COMMANDS")]
        wields = [w.name(t) for t, _ in w.out_edges(cid, "WIELDS")]
        life = f'{n["born"]} - {n["died"]} AS' if "died" in n else f'b. {n["born"]} AS'
        fate = f' · fell in {esc(n["died_in"])}' if n.get("died_in") else ""
        uri = w.image("portrait", cid)
        cards.append(f"""
<article class="card">
  {img_or_placeholder(uri, "Portrait of " + n["name"])}
  <div class="cardbody">
    <h3>{esc(n["name"])}</h3>
    <p class="tag">{esc(n.get("role", ""))} · {esc(", ".join(faction))} · {life}{fate}</p>
    <p class="dossier">{esc(d.get("dossier", ""))} {esc(d.get("appearance", ""))}</p>
    <p class="meta">{("commands " + esc(", ".join(commands))) if commands else "holds no command"}{(" · wields " + esc(", ".join(wields))) if wields else ""}</p>
  </div>
</article>""")
    minors = w.by_kind("character", tier="minor")
    by_faction = {}
    for m in minors:
        f = ", ".join(w.name(t) for t, _ in w.out_edges(m, "MEMBER_OF"))
        by_faction.setdefault(f, []).append(w.name(m))
    minor_rows = "".join(
        f"<tr><td>{esc(f)}</td><td>{esc(', '.join(sorted(names)))}</td></tr>"
        for f, names in sorted(by_faction.items()))
    return ("<h2>Dramatis personae</h2>"
            "<p class='lede'>Twelve major characters anchor the narrative; the wiki and registry track "
            "every named soul.</p>\n" + "\n".join(cards)
            + f"""<h3>The supporting cast ({len(minors)})</h3>
<div class="tablewrap"><table><tr><th>Faction</th><th>Members</th></tr>{minor_rows}</table></div>""")


def render_relics(w):
    cards = []
    for aid in w.by_kind("artifact"):
        n = w.nodes[aid]
        d = w.dossier(aid)
        wielder = [w.name(s) for s, _ in w.in_edges(aid, "WIELDS")]
        housed = [w.name(t) for t, _ in w.out_edges(aid, "HOUSED_IN")]
        uri = w.image("relic", aid)
        cards.append(f"""
<article class="card small">
  {img_or_placeholder(uri, n["name"])}
  <div class="cardbody">
    <h3>{esc(n["name"])}</h3>
    <p class="tag">{esc(n.get("artifact_class", ""))} · forged {esc(n.get("forged"))} AS</p>
    <p class="dossier">{esc(d.get("dossier", ""))}</p>
    <p class="meta">wielded by {esc(", ".join(wielder) or "no one living")} · kept at {esc(", ".join(housed))}</p>
  </div>
</article>""")
    beasts = []
    for bid in w.by_kind("creature"):
        n = w.nodes[bid]
        d = w.dossier(bid)
        lair = [w.name(t) for t, _ in w.out_edges(bid, "LAIRS_IN")]
        uri = w.image("creature", bid)
        beasts.append(f"""
<article class="card small">
  {img_or_placeholder(uri, n["name"])}
  <div class="cardbody">
    <h3>{esc(n["name"])}</h3>
    <p class="tag">{esc(n.get("habit", ""))}</p>
    <p class="dossier">{esc(d.get("dossier", ""))}</p>
    <p class="meta">lairs near {esc(", ".join(lair))}</p>
  </div>
</article>""")
    return ("<h2>Relics of the Sundering</h2>\n" + "\n".join(cards)
            + "\n<h2>The bestiary</h2>\n" + "\n".join(beasts))


def render_hidden(w):
    secrets = []
    for cid in w.by_kind("character", tier="major"):
        n = w.nodes[cid]
        if n.get("secret"):
            secrets.append(f"<tr><td>{esc(n['name'])}</td><td>{esc(n['secret'])}</td></tr>")
    truths = []
    for cid in sorted(w.by_kind("conflict"), key=lambda c: w.nodes[c]["began"]):
        n = w.nodes[cid]
        truths.append(f"<tr><td>{esc(n['name'])}</td><td>{esc(n.get('secret_truth', ''))}</td></tr>")
    disputes = []
    for d in w.plan["disputes"]:
        disputes.append(
            f"<tr><td>{esc(d['entity_name'])}</td><td>{esc(d['property'])}</td>"
            f"<td class='true'>{esc(d['true_value'])} AS</td><td class='false'>{esc(d['false_value'])} AS</td></tr>")
    n_vis = len(w.plan["visual_only"])
    n_chains = len(w.plan["chains"])
    return f"""
<h2>The hidden layer <span class="warnpill">judges only</span></h2>
<p class="lede">This is the part of the world built specifically to be hard: the machinery behind the
benchmark. Do not let this section travel beyond the judging group.</p>
<h3>What each character hides</h3>
<p>Every major character carries a secret that surfaces obliquely in diaries, interrogations, and
codex rumor columns.</p>
<div class="tablewrap"><table><tr><th>Character</th><th>Secret</th></tr>{''.join(secrets)}</table></div>
<h3>What the chronicles will not say</h3>
<p>Each conflict has an official account and a buried truth.</p>
<div class="tablewrap"><table><tr><th>Conflict</th><th>Buried truth</th></tr>{''.join(truths)}</table></div>
<h3>Deliberately disputed facts</h3>
<p>For the agentic track, these values are contradicted on purpose: the true year exists only in the
canonical codex entry, while ballads and broadsheets assert the false one with total confidence.</p>
<div class="tablewrap"><table><tr><th>Entity</th><th>Fact</th><th>True</th><th>False (planted)</th></tr>{''.join(disputes)}</table></div>
<h3>Also engineered</h3>
<p>{n_vis} numeric facts exist only inside figure plates (never in any text), and {n_chains} two-hop
fact chains are split so that no single document can answer their questions alone.</p>
"""


def render_validation(w):
    if not w.validation:
        return ("<h2>Corpus validation</h2><p class='lede'>No validation report found for this run. "
                "Run <code>scripts/validate_corpus.py</code> and rebuild this page.</p>")
    v = w.validation
    ok_all = v["verdict"] == "GO"
    rows = "".join(
        f"<tr><td>{esc(r['check'])}</td>"
        f"<td>{'<span class=passpill>PASS</span>' if r['ok'] else '<span class=failpill>FAIL</span>'}</td>"
        f"<td>{esc(r['detail'])}</td></tr>"
        for r in v["checks"])
    b = v.get("benchmark", {})
    tracks = " · ".join(f"{k.split('_')[0]}: {n}" for k, n in b.get("tracks", {}).items())
    return f"""
<h2>Corpus validation <span class="{'passpill' if ok_all else 'failpill'}">{esc(v['verdict'])}</span></h2>
<p class="lede">Before distribution, an automated gate re-checks every benchmark-critical guarantee
against the final generated text, not the plan. Image-only values must appear in no text document,
each multi-hop chain's two facts must never share a document, every planted false claim must exist,
each disputed truth must live only in its canonical entry, and every question's evidence files must
resolve inside the public corpus. A question whose evidence is not airtight is dropped automatically.</p>
<div class="statgrid">
  <div><b>{v['documents']}</b><span>documents</span></div>
  <div><b>{v['words']:,}</b><span>words (~{v['pages_approx']:,} pages)</span></div>
  <div><b>{b.get('dev', 0) + b.get('eval', 0)}</b><span>verified questions</span></div>
  <div><b>{b.get('dev', 0)}</b><span>released as dev set</span></div>
  <div><b>{b.get('eval', 0)}</b><span>held out for judging</span></div>
  <div><b>{b.get('rejected', 0)}</b><span>auto-rejected</span></div>
</div>
<p class="meta">Question mix: {esc(tracks)} · source run: {esc(v['run_dir'])}</p>
<div class="tablewrap"><table><tr><th>Check</th><th>Result</th><th>Detail</th></tr>{rows}</table></div>
"""


def build_graph_json(w):
    KEEP = {"character": ["role", "tier", "born", "died"],
            "location": ["region", "founded", "status", "is_core"],
            "artifact": ["artifact_class", "forged"],
            "conflict": ["began", "ended", "victor", "outcome"],
            "faction": ["org_kind", "doctrine"], "creature": ["habit"]}
    nodes = [{"id": nid, "name": n["name"], "kind": n["kind"],
              "p": {k: n[k] for k in KEEP.get(n["kind"], []) if k in n}}
             for nid, n in w.nodes.items()]
    seen, links = set(), []
    for e in w.links:
        key = (e["source"], e["target"], e["relation"])
        if key in seen:
            continue
        seen.add(key)
        links.append({"s": e["source"], "t": e["target"], "r": e["relation"]})
    return json.dumps({"nodes": nodes, "links": links}, ensure_ascii=False).replace("</", "<\\/"), len(nodes), len(links)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run_dir", required=True)
    ap.add_argument("--out", default=os.path.join("share", "ashen_era_companion.html"))
    ap.add_argument("--assets", choices=["embed", "files"], default="embed",
                    help="embed = images inlined as data URIs (single file); "
                         "files = images written to an images/ folder next to the page")
    args = ap.parse_args()

    out_abs = os.path.abspath(args.out)
    assets_out = os.path.join(os.path.dirname(out_abs), "images")
    if args.assets == "files":
        os.makedirs(assets_out, exist_ok=True)
    w = World(os.path.abspath(args.run_dir), assets_mode=args.assets, assets_out=assets_out)
    graph_json, n_nodes, n_links = build_graph_json(w)
    sections = {
        "world": render_overview(w),
        "factions": render_factions(w),
        "conflicts": render_conflicts(w),
        "characters": render_characters(w),
        "relics": render_relics(w),
        "hidden": render_hidden(w),
        "validation": render_validation(w),
    }
    tpl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "companion_template.html")
    with open(tpl_path, encoding="utf-8") as f:
        page = f.read()
    page = page.replace("__DATA__", graph_json)
    page = page.replace("__STATS__", f"{n_nodes} entities / {n_links} relations / era 212-468 AS / run {os.path.basename(w.run_dir)}")
    for key, htm in sections.items():
        page = page.replace(f"__SEC_{key.upper()}__", htm)

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(page)
    if args.assets == "files":
        # Standalone package: give the page a full HTML skeleton so it opens
        # directly from disk, and report the copied asset files.
        cut = page.index("</style>") + len("</style>")
        page = ("<!doctype html>\n<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">\n"
                + page[:cut] + "\n</head>\n<body>" + page[cut:] + "\n</body>\n</html>\n")
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(page)
        n_files = len(os.listdir(assets_out)) if os.path.isdir(assets_out) else 0
        print(f"Wrote {args.out} ({len(page)/1024:.0f} KB) + {n_files} image files in images/")
        return
    n_imgs = page.count("data:image/jpeg")
    print(f"Wrote {args.out} ({len(page)/1024:.0f} KB, {n_imgs} embedded images)")
    if n_imgs == 0:
        print("Note: no atmospheric images found in the run yet; rerun after the images stage to embed them.")


if __name__ == "__main__":
    main()
