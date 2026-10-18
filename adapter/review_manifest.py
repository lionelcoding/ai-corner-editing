#!/usr/bin/env python3
"""Adaptateur générique pour ai-corner-editing.

Lit <projet>/review.config.json, écrit <projet>/review/manifest.json (stage "final" ou "storyboard").
Usage :
  review_manifest.py <projet>                 # (ré)écrit le manifeste du tour en cours
  review_manifest.py <projet> --next-round    # passe au tour suivant (après « applique la relecture »)
  review_manifest.py <projet> --video out/autre.mp4   # remplace la vidéo du config

review.config.json (chemins relatifs à la racine du projet) :
{
  "project": "mon-projet", "title": "…", "stage": "final",
  "canvas": {"w": 1080, "h": 1920, "fps": 30},
  "video": "out/rendu.mp4",                         # vidéo relue (stage final) ou animatique (storyboard)
  "audio_track": true,                              # piste forme d'onde de la vidéo
  "segments": [{"id","label","start","end","text"?}],          # plans / scènes
  "components": [{"id","label","start","end","rid"?,"bbox"?,"source"?}],  # éléments cliquables
  "regions":  [{"id","label","start","end","bbox"}],            # zones sans HTML (face cam incrustée…)
  "captions": {"from": "hyperframes-subs"|"whisper"|"json", "file": "…", "offset": 0,
               "bbox": [x,y,w,h], "zones": [{"before": 14.41, "bbox": [...]}]},
  "sfx":      {"from": "mixpy"|"json", "file": "…", "offset": 0} | [{"id","label","start","end"?}],
  "html_layer": {"src": "index.html", "timeline": "main", "track": "components", "rect": [0,0,1080,1920],
                 "vars": {"arrows": true}},          # optionnel : variables HyperFrames -> copie index.review.html
  "panels": [...],                                   # stage storyboard : panneaux au format du schéma
  "version": "V2 · coupe Premiere"                   # nom du tour affiché dans le menu Versions de l'app
}
Un tour qui se termine (--next-round) est archivé dans review/versions/round-N.json ; --archive-config reconstitue un ancien tour.
"""
import argparse, json, os, re, sys

def rel(review_dir, project_dir, p):
    """Chemin relatif au dossier review/ (exigé par le manifeste)."""
    return os.path.relpath(os.path.join(project_dir, p), review_dir)

def captions(cfg, project):
    src, items = cfg.get("from"), []
    path = os.path.join(project, cfg["file"]); off = float(cfg.get("offset", 0))
    def bbox_at(t):
        for z in cfg.get("zones", []):
            if t < z["before"]: return z["bbox"]
        return cfg.get("bbox")
    words = []                                      # (mot, début, fin, mot-clé)
    if src == "hyperframes-subs":                   # window.SUBS=[{t,end,w:[[mot,t,k],…]}]
        raw = open(path, encoding="utf-8").read()
        chunks = json.loads(raw[raw.index("["): raw.rindex("]") + 1])
        for c in chunks:
            ws = c["w"]
            for i, (w, t, k) in enumerate(ws):
                e = ws[i + 1][1] if i + 1 < len(ws) else c["end"]
                words.append((w, t + off, e + off, bool(k)))
    elif src == "whisper":                          # transcription verbose_json avec "words"
        for w in json.load(open(path, encoding="utf-8"))["words"]:
            words.append((w["word"], w["start"] + off, w["end"] + off, False))
    elif src == "json":                             # [{"word","start","end"}]
        for w in json.load(open(path, encoding="utf-8")):
            words.append((w["word"], w["start"] + off, w["end"] + off, False))
    else:
        sys.exit(f"captions.from inconnu : {src}")
    for i, (w, s, e, k) in enumerate(words):
        it = {"id": f"cap-{i:04d}", "label": w, "text": w, "start": round(s, 3), "end": round(max(e, s + 0.05), 3)}
        b = bbox_at(s)
        if b: it["bbox"] = b
        if k: it["data"] = {"keyword": True}
        it["source"] = {"file": rel_src(cfg["file"])}
        items.append(it)
    return items

def rel_src(p):  # sources : chemins relatifs au projet, lisibles par Claude
    return p

def sfx(cfg, project):
    if isinstance(cfg, list):
        return [dict(x) for x in cfg]
    path = os.path.join(project, cfg["file"]); off = float(cfg.get("offset", 0)); items = []
    if cfg.get("from") == "mixpy":                  # tuples ("assets/sfx/x.mp3", t, vol, ss, dur) + boucles "for t in (…)"
        txt = open(path, encoding="utf-8").read()
        block = txt[txt.index("SFX"): txt.index("]]", txt.index("SFX")) + 2] if "SFX" in txt else ""
        for m in re.finditer(r'\("([^"]+)",\s*([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+|None)\)', block):
            name = os.path.splitext(os.path.basename(m.group(1)))[0]; t = float(m.group(2)) + off
            d = float(m.group(5)) if m.group(5) != "None" else 0.6
            items.append((name, t, d))
        for m in re.finditer(r'\("([^"]+)",\s*t,\s*[\d.]+,\s*[\d.]+,\s*(?:[\d.]+|None)\)\s*for t in \(([^)]*)\)', block):
            name = os.path.splitext(os.path.basename(m.group(1)))[0]
            for v in m.group(2).split(","):
                if v.strip(): items.append((name, float(v) + off, 0.6))
        for m in re.finditer(r'\("([^"]+)",\s*round\(([\d.]+)\s*\*\s*i,\s*2\)[^)]*\)\s*for i in range\((\d+),\s*(\d+)\)', block):
            name = os.path.splitext(os.path.basename(m.group(1)))[0]
            for i in range(int(m.group(3)), int(m.group(4))): items.append((name, float(m.group(2)) * i + off, 0.3))
        items.sort(key=lambda x: x[1])
        return [{"id": f"sfx-{i:03d}-{n}", "label": n, "start": round(t, 3), "end": round(t + d, 3),
                 "source": {"file": cfg["file"]}} for i, (n, t, d) in enumerate(items)]
    if cfg.get("from") == "json":
        return json.load(open(path, encoding="utf-8"))
    sys.exit("sfx.from inconnu")

def build(cfg, project, review, rnd, video=None):
    stage = cfg.get("stage", "final")
    m = {"schema": 1, "project": cfg["project"], "round": rnd, "stage": stage, "canvas": cfg["canvas"]}
    if cfg.get("title"): m["title"] = cfg["title"]
    if cfg.get("notes"): m["notes"] = cfg["notes"]
    if cfg.get("chapters"): m["chapters"] = cfg["chapters"]
    video = video or cfg.get("video")
    if video: m["media"] = {"video": rel(review, project, video)}
    if stage == "storyboard":
        panels = json.loads(json.dumps(cfg.get("panels", [])))   # chemins d'images / clips relatifs à review/
        for pn in panels:
            pn["images"] = [rel(review, project, im) if isinstance(im, str) else {**im, "src": rel(review, project, im["src"])}
                            for im in pn.get("images", [])]
            if pn.get("clip", {}).get("src"): pn["clip"]["src"] = rel(review, project, pn["clip"]["src"])
        m["panels"] = panels
    tracks = []
    if cfg.get("segments"):
        tracks.append({"id": "segments", "label": "Plans", "kind": "segment", "items": cfg["segments"]})
    if cfg.get("components"):
        tracks.append({"id": "components", "label": "Éléments", "kind": "component", "items": cfg["components"]})
    if cfg.get("regions"):
        tracks.append({"id": "regions", "label": "Zones", "kind": "region", "items": cfg["regions"]})
    if cfg.get("captions"):
        tracks.append({"id": "captions", "label": "Sous-titres", "kind": "word", "items": captions(cfg["captions"], project)})
    if cfg.get("sfx"):
        tracks.append({"id": "sfx", "label": "Effets sonores", "kind": "audio-cue", "items": sfx(cfg["sfx"], project)})
    if cfg.get("audio_track", True) and video:
        tracks.append({"id": "mix", "label": "Son", "kind": "audio", "src": rel(review, project, video)})
    if tracks: m["tracks"] = tracks
    if cfg.get("html_layer"):
        h = dict(cfg["html_layer"]); h["kind"] = "html"
        if h.get("vars"):                           # variables HyperFrames (ex. {"arrows": true}) : copie <nom>.review.html
            src = os.path.join(project, h["src"]); dst = os.path.splitext(src)[0] + ".review.html"
            shim = ("<script>window.__hyperframes=Object.assign(window.__hyperframes||{},{getVariables:()=>(%s)});</script>"
                    % json.dumps(h.pop("vars")))
            html = open(src, encoding="utf-8").read()
            i = html.lower().find("<head>"); html = html[:i + 6] + shim + html[i + 6:] if i >= 0 else shim + html
            open(dst, "w", encoding="utf-8").write(html); h["src"] = os.path.relpath(dst, project)
        h["src"] = rel(review, project, h["src"])
        h.setdefault("size", [cfg["canvas"]["w"], cfg["canvas"]["h"]]); h.setdefault("rect", [0, 0, cfg["canvas"]["w"], cfg["canvas"]["h"]])
        m["layers"] = [h]
    if cfg.get("duration"): m["duration"] = cfg["duration"]
    return m, tracks

def label(review, rnd, text):
    """Nom lisible d'un tour, dans review/versions/index.json (le manifeste n'accepte pas de champ en plus)."""
    if not text: return
    d = os.path.join(review, "versions"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "index.json"); idx = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
    idx[str(rnd)] = text; json.dump(idx, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("project"); ap.add_argument("--next-round", action="store_true"); ap.add_argument("--video")
    ap.add_argument("--archive-config", help="reconstituer un ancien tour à partir d'une config sauvegardée")
    ap.add_argument("--round", type=int, help="numéro du tour à reconstituer (avec --archive-config)")
    ap.add_argument("--label", help="nom de la version (sinon clé \"version\" de la config)")
    a = ap.parse_args()
    project = os.path.abspath(a.project)
    review = os.path.join(project, "review"); os.makedirs(review, exist_ok=True)
    if a.archive_config:                            # tour passé -> review/versions/round-N.json, sans toucher au tour courant
        cfg = json.load(open(a.archive_config, encoding="utf-8"))
        m, _ = build(cfg, project, review, a.round, a.video)
        d = os.path.join(review, "versions"); os.makedirs(d, exist_ok=True)
        json.dump(m, open(os.path.join(d, f"round-{a.round}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        label(review, a.round, a.label or cfg.get("version"))
        print(f"archivé : tour {a.round} · {a.label or cfg.get('version') or ''}"); return
    cfg_path = os.path.join(project, "review.config.json")
    if not os.path.exists(cfg_path): sys.exit(f"Pas de review.config.json dans {project}")
    cfg = json.load(open(cfg_path, encoding="utf-8"))
    out = os.path.join(review, "manifest.json")
    rnd = 1
    new_stage = cfg.get("stage", "final")
    if a.round and not a.archive_config:          # numéro imposé (ex. relecture finale qui suit 4 tours de storyboard)
        rnd = a.round
    elif os.path.exists(out):
        old = json.load(open(out, encoding="utf-8")); rnd = old.get("round", 1)
        if old.get("stage") and old["stage"] != new_stage:
            # passage storyboard -> final (ou retour) : on garde l'étape précédente consultable (onglet de l'app + menu Versions)
            json.dump(old, open(os.path.join(review, f"manifest.{old['stage']}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            d = os.path.join(review, "versions"); os.makedirs(d, exist_ok=True)
            json.dump(old, open(os.path.join(d, f"round-{rnd}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            rnd += 1
            print(f"étape {old['stage']} gardée (manifest.{old['stage']}.json + version {rnd - 1}) · {new_stage} commence au tour {rnd}")
        elif a.next_round:                          # on archive le tour qui se termine avant de l'écraser
            d = os.path.join(review, "versions"); os.makedirs(d, exist_ok=True)
            json.dump(old, open(os.path.join(d, f"round-{rnd}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            rnd += 1
    m, tracks = build(cfg, project, review, rnd, a.video)
    json.dump(m, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    label(review, rnd, a.label or cfg.get("version"))
    n = {t["id"]: len(t.get("items", [])) for t in tracks}
    print(f"OK {out} · tour {rnd} · {m['stage']} · pistes {n}" + (f" · {a.label or cfg.get('version')}" if (a.label or cfg.get("version")) else ""))

if __name__ == "__main__":
    main()
