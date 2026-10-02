#!/usr/bin/env python3
"""Extraits de calibration des « euh » (METHODE.md, étape 3) :
pour chaque fenêtre de 30 s, l'audio d'origine (avant) et l'audio coupé selon l'EDL v3 (après),
plus le texte aligné avec les coupes marquées. usage: calib.py"""
import json, os, subprocess, wave
import numpy as np

SR = 48000
BASE = os.path.expanduser(os.environ.get("CAFE_IA_DIR", "~/Files/cafe-ia"))  # dossier des épisodes
OUT = os.path.join(BASE, "calibration-euh-2026-10-01")
os.makedirs(OUT, exist_ok=True)
WINDOWS = [("2026-09-24-cafe-ia-002", 1359.0, "Baptiste explique le premier batch"),
           ("2026-09-24-cafe-ia-002", 618.0, "Luc explique la base de connaissance"),
           ("2026-09-18-cafe-ia-001", 541.0, "Baptiste sur le montage chiant")]


def pcm(path, a, d):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-ss", str(a), "-t", str(d), "-i", path,
                          "-ar", str(SR), "-ac", "2", "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).reshape(-1, 2).astype(np.float32)


def save(x, path):
    tmp = path + ".wav"
    w = wave.open(tmp, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes(np.clip(x, -32768, 32767).astype(np.int16).tobytes()); w.close()
    subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", tmp, "-af", "loudnorm=I=-16:TP=-1",
                    "-c:a", "aac", "-b:a", "160k", path], check=True)
    os.remove(tmp)


md = ["# Calibration des « euh » — 3 extraits de 30 s", "",
      "Pour chaque extrait : écouter « avant » puis « après ». Question : les coupes tombent-elles sur de vraies hésitations, sans manger de mot ni de respiration utile ? Les coupes sont marquées ✂ dans le texte.", ""]
for n, (ep, a, label) in enumerate(WINDOWS, 1):
    d = os.path.join(BASE, ep)
    edl = json.load(open(os.path.join(d, "work", "edl-long-v3.json")))
    mix = os.path.join(d, f"{ep}-audio-mix.m4a")
    b = a + 30.0
    src = pcm(mix, a, 30.0)
    f = int(0.006 * SR); ramp = np.linspace(0, 1, f, dtype=np.float32)[:, None]
    parts = []
    for k in edl["keep"]:
        s, e = max(k["in"], a), min(k["out"], b)
        if e - s <= 0.01:
            continue
        x = src[int((s - a) * SR):int((e - a) * SR)].copy()
        if len(x) > 2 * f:
            x[:f] *= ramp; x[-f:] *= ramp[::-1]
        parts.append(x)
    after = np.vstack(parts) if parts else src[:0]
    mm = f"{int(a) // 60:02d}m{int(a) % 60:02d}"
    save(src, os.path.join(OUT, f"{n}-{ep[-3:]}-{mm}-avant.m4a"))
    save(after, os.path.join(OUT, f"{n}-{ep[-3:]}-{mm}-apres.m4a"))
    cuts = [r for r in edl["removed"] if r["in"] < b and r["out"] > a]
    words = []
    for pth in ("aligned-luc.json", "aligned-baptiste.json"):
        words += [w for w in json.load(open(os.path.join(d, "work", pth))) if a <= w["t0"] < b]
    ev = [(w["t0"], f"{w['w']}", w["spk"]) for w in words] + [(r["in"], f"✂[{'euh' if 'euh' in r['why'] else 'silence'} {r['out'] - r['in']:.2f} s]", None) for r in cuts]
    ev.sort()
    txt, spk = [], None
    for t, w, s in ev:
        if s and s != spk:
            txt.append(f"\n**{s}** :"); spk = s
        txt.append(w)
    neuh = sum(1 for r in cuts if "euh" in r["why"])
    md += [f"## {n}. {label} — Café IA #{int(ep[-3:])} à {mm} ({len(after) / SR:.1f} s après coupe, {neuh} « euh » coupés)", "",
           " ".join(txt).strip(), ""]
open(os.path.join(OUT, "calibration.md"), "w").write("\n".join(md))
print("CALIB-FIN", OUT)
