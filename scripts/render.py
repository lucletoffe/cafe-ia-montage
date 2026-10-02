#!/usr/bin/env python3
"""Montage d'un épisode (METHODE.md, étapes 5-6) : EDL macro (spec éditoriale)
+ micro-coupes calées sur l'énergie audio par piste, audio assemblé à l'échantillon avec
micro-fondus, vidéo sélectionnée sur la même grille d'images, sous-titres, chapitres.
Échelle de temps de référence = audio serveur Jitsi (t=0 au début de l'enregistrement).
usage: render.py spec.json [long|shorts|all|edl]"""
import json, os, subprocess, sys, wave
import numpy as np

FPS, SR = 30, 48000
spec = json.load(open(sys.argv[1]))
what = sys.argv[2] if len(sys.argv) > 2 else "all"
D = os.path.expanduser(spec["dir"])
WORK, MONT = os.path.join(D, "work"), os.path.join(D, "montages")
os.makedirs(WORK, exist_ok=True); os.makedirs(MONT, exist_ok=True)
P = lambda p: os.path.join(D, os.path.expanduser(p))
import re
HALLU = re.compile(r"sous-titr|radio-canada|amara\.org|ST' ?501|merci d'avoir regardé", re.I)
SEGS = []
for src in spec["segments"]:
    dat = json.load(open(P(src["path"])))
    rows = dat["timeline"] if src["kind"] == "timeline" else dat
    for r in rows:
        spk = src.get("spk") or ("Luc" if "luc" in r["speaker"].lower() else "Baptiste")
        t = (r.get("text") or "").strip()
        if t and not HALLU.search(t) and t.lower() not in ("merci.", "merci", "merci beaucoup."):
            SEGS.append({"spk": spk, "start": float(r["start"]), "end": float(r["end"]), "text": t})
SEGS.sort(key=lambda r: r["start"])
# mots de sous-titre : texte du segment, temps réparti au prorata des caractères
words = []
for r in SEGS:
    toks = r["text"].split()
    n = max(sum(len(x) + 1 for x in toks), 1)
    pos = 0
    for x in toks:
        t0 = r["start"] + (r["end"] - r["start"]) * pos / n
        pos += len(x) + 1
        words.append({"spk": r["spk"], "w": x, "t0": t0, "t1": r["start"] + (r["end"] - r["start"]) * pos / n})
words.sort(key=lambda w: w["t0"])
ALIGNED = []
for pth in spec.get("aligned", []):
    if os.path.exists(P(pth)):
        ALIGNED += [w for w in json.load(open(P(pth))) if w["t1"] > w["t0"]]
if ALIGNED:
    ALIGNED.sort(key=lambda w: w["t0"])
    words = ALIGNED
print(f"{len(SEGS)} segments serveur, {len(words)} mots ({'alignés MMS_FA' if ALIGNED else 'au prorata'})", flush=True)


def euh_gaps(a, b):
    """trous entre deux mots alignés consécutifs du même locuteur où sa voix est active = hésitation"""
    out = []
    if not ALIGNED:
        return out
    by = {}
    for w in ALIGNED:
        if a - 1 <= w["t0"] <= b + 1:
            by.setdefault(w["spk"], []).append(w)
    others = {s: [(w["t0"], w["t1"]) for w in ALIGNED if w["spk"] != s and a - 1 <= w["t0"] <= b + 1] for s in by}
    for spk, ws in by.items():
        for w, nx in zip(ws, ws[1:]):
            g0, g1 = w["t1"], nx["t0"]
            if not (0.25 <= g1 - g0 <= 2.5):
                continue
            act = ACT[spk][int(g0 * 100):int(g1 * 100)]
            if not len(act) or act.mean() < 0.6:
                continue
            if any(o0 < g1 and o1 > g0 for o0, o1 in others[spk]):
                continue
            out.append((g0 + 0.04, g1 - 0.04, spk))
    return out


def pcm(path, sr, ch):
    raw = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-i", path, "-ar", str(sr), "-ac", str(ch),
                          "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).reshape(-1, ch)


# --- activité vocale par piste (trames de 10 ms) ---
ACT = {}
for tr in spec["tracks"]:
    a = pcm(P(tr["wav"]), 16000, 1)[:, 0].astype(np.float32)
    n = len(a) // 160
    db = 20 * np.log10(np.sqrt((a[:n * 160].reshape(n, 160) ** 2).mean(1)) + 1.0)
    thr = max(np.percentile(db, 20) + 12, np.percentile(db, 97) - 32)
    act = db > thr
    k = 15  # maintien 150 ms
    act = np.convolve(act.astype(int), np.ones(k, int), "same") > 0
    ACT[tr["spk"]] = act
    print(f"piste {tr['spk']} : seuil {thr:.1f} dB, active {act.mean() * 100:.0f} %", flush=True)
NFR = max(len(v) for v in ACT.values())
ANY = np.zeros(NFR, bool)
for v in ACT.values():
    ANY[:len(v)] |= v


def runs(mask, a, b):
    """plages inactives (False) de mask entre a et b (secondes)"""
    i0, i1 = int(a * 100), min(int(b * 100), len(mask))
    out, start = [], None
    for i in range(i0, i1):
        if not mask[i]:
            start = i if start is None else start
        elif start is not None:
            out.append((start / 100, i / 100)); start = None
    if start is not None:
        out.append((start / 100, i1 / 100))
    return out


def speaker_at(t, before):
    i = int(t * 100)
    rng = range(i - 1, max(i - 300, 0), -1) if before else range(i, min(i + 300, NFR))
    for j in rng:
        for s, v in ACT.items():
            if j < len(v) and v[j]:
                return s
    return None


def snap_range(a, b):
    i = int(a * 100)
    if i < NFR and ANY[i]:
        j = i
        while j > 0 and ANY[j - 1] and i - j < 200:
            j -= 1
    else:
        j = i
        while j < min(int(b * 100), NFR) and not ANY[j]:
            j += 1
    k = int(b * 100)
    if k < NFR and ANY[k]:
        e = k
        while e < NFR and ANY[e] and e - k < 300:
            e += 1
    else:
        e = k
        while e > j and not ANY[e - 1]:
            e -= 1
    return j / 100 - 0.08, e / 100 + 0.12


def micro_cuts(a, b, sil_cap):
    cuts = []
    for s0, s1 in runs(ANY, a, b):
        d = s1 - s0
        if d <= (0.6 if sil_cap >= 0.25 else 0.4):
            continue
        prev, nxt = speaker_at(s0, True), speaker_at(s1, False)
        cap, why = sil_cap, "micro · silence"
        before = [r for r in SEGS if s0 - 1.5 <= r["end"] <= s0 + 0.3]
        next_segs = [r for r in SEGS if r["spk"] == nxt and s1 - 0.5 <= r["start"] <= s1 + 1.0]
        if nxt and prev and nxt != prev and not next_segs:
            cap, why = 1.2, "silence utile · réaction de l'autre"
        elif before and before[-1]["text"].rstrip().endswith("?"):
            cap, why = 1.2, "silence utile · après une question"
        if d > cap:
            cuts.append((s0 + cap / 2, s1 - cap / 2, why))
    for g0, g1, spk in euh_gaps(a, b):
        cuts.append((g0, g1, "micro · euh"))
    cuts.sort()
    merged = []
    for c in cuts:
        if merged and c[0] <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], c[1]), merged[-1][2])
        else:
            merged.append(c)
    return merged


def build(ranges, sil_cap):
    keep, removed = [], []
    prev_end = None
    for r in ranges:
        a, b = snap_range(r["in"], r["out"])
        if prev_end is not None and a < prev_end:
            a = prev_end
        if prev_end is not None and a > prev_end:
            removed.append({"in": round(prev_end, 3), "out": round(a, 3), "why": r.get("removed_before", "macro · hors angle")})
        cuts = micro_cuts(a, b, sil_cap)
        t = a
        for c0, c1, why in cuts:
            if c0 - t >= 0.05:
                keep.append([t, c0, r["why"]])
            removed.append({"in": round(c0, 3), "out": round(c1, 3), "why": why})
            t = c1
        keep.append([t, b, r["why"]])
        prev_end = b
    # garde-fou anti-hachage : segment conservé >= 1 s (on rend la coupe suivante)
    i = 0
    while i < len(keep) - 1:
        if keep[i][1] - keep[i][0] < 1.0 and abs(keep[i + 1][0] - keep[i][1]) < 2.5:
            keep[i][1] = keep[i + 1][1]
            del keep[i + 1]
        else:
            i += 1
    seg = []
    for s, e, why in keep:
        s, e = round(s * FPS) / FPS, round(e * FPS) / FPS
        if e - s >= 2 / FPS:
            seg.append((s, e, why))
    return seg, removed


def remap(seg):
    acc, m = 0.0, []
    for s, e, _ in seg:
        m.append((s, e, acc)); acc += e - s
    return m, acc


def to_out(m, t):
    for k, (s, e, o) in enumerate(m):
        if s <= t <= e:
            return o + t - s
        if t < s:
            if k and s - m[k - 1][1] < 3.0:
                return o
            return None
    return None


def captions(seg, max_words, max_chars, max_dur):
    m, _ = remap(seg)
    lines, cur = [], None
    for w in words:
        o0 = to_out(m, w["t0"])
        if o0 is None:
            continue
        o1 = to_out(m, w["t1"])
        o1 = o1 if o1 is not None and o1 > o0 else o0 + 0.3
        if cur and (cur["spk"] != w["spk"] or len(cur["w"]) >= max_words or len(" ".join(cur["w"])) + len(w["w"]) > max_chars
                    or o1 - cur["o0"] > max_dur or o0 - cur["o1"] > 0.7):
            lines.append(cur); cur = None
        if cur:
            cur["w"].append(w["w"]); cur["o1"] = o1
        else:
            cur = {"spk": w["spk"], "w": [w["w"]], "o0": o0, "o1": o1}
    if cur:
        lines.append(cur)
    for i in range(len(lines) - 1):
        lines[i]["o1"] = min(max(lines[i]["o1"], lines[i]["o0"] + 0.5), lines[i + 1]["o0"])
    return lines


def fmt_srt(t):
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def fmt_ass(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def write_srt(lines, path, spk=True):
    with open(path, "w") as f:
        for i, l in enumerate(lines, 1):
            f.write(f"{i}\n{fmt_srt(l['o0'])} --> {fmt_srt(l['o1'])}\n{(l['spk'] + ' : ') if spk else ''}{' '.join(l['w'])}\n\n")


def write_ass(lines, path):
    with open(path, "w") as f:
        f.write("[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 0\n\n"
                "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
                "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
                "Alignment, MarginL, MarginR, MarginV, Encoding\n"
                "Style: Cap,Liberation Sans,62,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,70,70,0,1\n\n"
                "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
        for l in lines:
            f.write(f"Dialogue: 0,{fmt_ass(l['o0'])},{fmt_ass(l['o1'])},Cap,,0,0,0,,{' '.join(l['w']).replace('{', '(').replace('}', ')')}\n")


MIX = None


def audio_wav(seg, path):
    global MIX
    if MIX is None:
        MIX = pcm(P(spec["mix"]), SR, 2)
    f = int(0.006 * SR)
    ramp = np.linspace(0, 1, f, dtype=np.float32)[:, None]
    parts = []
    for s, e, _ in seg:
        n0, n1 = int(round(s * SR)), int(round(e * SR))
        x = MIX[n0:n1].astype(np.float32)
        if len(x) < n1 - n0:
            x = np.vstack([x, np.zeros((n1 - n0 - len(x), 2), np.float32)])
        if len(x) > 2 * f:
            x[:f] *= ramp; x[-f:] *= ramp[::-1]
        parts.append(x)
    y = np.clip(np.vstack(parts), -32768, 32767).astype(np.int16)
    w = wave.open(path, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes()); w.close()


def render(seg, layout, path, ass=None):
    if not spec.get("videos"):
        path = path[:-4] + ".m4a"
        wav = os.path.join(WORK, os.path.basename(path) + ".audio.wav")
        audio_wav(seg, wav)
        r = subprocess.run(["ffmpeg", "-nostdin", "-v", "error", "-y", "-i", wav, "-af", "loudnorm=I=-14:TP=-1:LRA=11",
                            "-c:a", "aac", "-b:a", "160k", path], capture_output=True, text=True)
        os.remove(wav)
        if r.returncode:
            print(r.stderr[-2000:]); raise SystemExit(f"échec {path}")
        d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                 capture_output=True, text=True).stdout)
        print(f"OK {os.path.basename(path)}  {d:.1f} s  {len(seg)} segments (audio seul)", flush=True)
        return
    t0, t_end = seg[0][0], seg[-1][1]
    terms = [f"between(t,{s - t0 - 0.25 / FPS:.6f},{e - t0 - 0.5 / FPS:.6f})" for s, e, _ in seg]
    # l'évaluateur ffmpeg limite la profondeur : paquets de 25 termes entre parenthèses
    expr = "+".join("(" + "+".join(terms[i:i + 25]) + ")" for i in range(0, len(terms), 25))
    lay, g, args = spec["layouts"][layout], [], []
    for p in lay:  # une entrée par panneau (une même vidéo peut fournir deux cadrages)
        v = spec["videos"][p["src"]]
        ss = t0 - v["offset"]
        if ss < 0:
            raise SystemExit(f"{p['src']} ne couvre pas t={t0:.1f}")
        args += ["-ss", f"{ss:.4f}", "-i", P(v["path"])]
    wav = os.path.join(WORK, os.path.basename(path) + ".audio.wav")
    audio_wav(seg, wav)
    a_idx = len(lay)
    args += ["-i", wav]
    for i, p in enumerate(lay):
        g.append(f"[{i}:v]fps={FPS},trim=duration={t_end - t0 + 1:.3f},select='{expr}',setpts=N/{FPS}/TB,{p['vf']}[p{i}]")
    if layout == "short":
        g.append("color=c=0x12141a:s=1080x160:r=30[band]")
        g.append("[p0][band][p1]vstack=inputs=3:shortest=1[base]")
    elif len(lay) == 2:
        g.append("[p0][p1]hstack=inputs=2:shortest=1[base]")
    else:
        g.append("[p0]null[base]")
    sub = f",subtitles='{ass}'" if ass else ""
    g.append(f"[base]format=yuv420p{sub}[v]")
    g.append(f"[{a_idx}:a]loudnorm=I=-14:TP=-1:LRA=11,aresample=48000[a]")
    script = os.path.join(WORK, os.path.basename(path) + ".filter")
    open(script, "w").write(";\n".join(g))
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-y", *args, "-/filter_complex", script, "-map", "[v]", "-map", "[a]",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "160k", "-shortest",
           "-movflags", "+faststart", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(wav)
    if r.returncode:
        print(r.stderr[-3000:]); raise SystemExit(f"échec {path}")
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                             capture_output=True, text=True).stdout)
    lufs = subprocess.run(["ffmpeg", "-nostdin", "-i", path, "-map", "0:a", "-af", "ebur128", "-f", "null", "-"],
                          capture_output=True, text=True).stderr
    li = [l for l in lufs.splitlines() if l.strip().startswith("I:")]
    print(f"OK {os.path.basename(path)}  {d:.1f} s  {len(seg)} segments  {li[-1].strip() if li else ''}", flush=True)


def edl(seg, removed, path):
    json.dump({"fps": FPS, "timescale": "audio serveur Jitsi (s)", "videos": spec["videos"],
               "keep": [{"in": s, "out": e, "why": w} for s, e, w in seg], "removed": removed},
              open(path, "w"), ensure_ascii=False, indent=1)


def write_verbatim(path):
    if not ALIGNED:
        return
    rng = (spec["keep"][0]["in"], spec["keep"][-1]["out"])
    eu = {round(g0, 2): (g0, g1) for g0, g1, _ in euh_gaps(*rng)}
    lines, cur, last = [], None, None
    for w in ALIGNED:
        if not (rng[0] <= w["t0"] <= rng[1]):
            continue
        if last is not None:
            sil = [r for r in runs(ANY, last, w["t0"]) if r[1] - r[0] > 0.6]
            for r in sil:
                cur["txt"].append(f"[· {r[1] - r[0]:.1f} s]")
            for k, (g0, g1) in eu.items():
                if last - 0.05 <= g0 <= w["t0"] and cur and cur["spk"] == w["spk"]:
                    cur["txt"].append(f"[euh {g1 - g0:.1f} s]")
        if not cur or cur["spk"] != w["spk"]:
            cur = {"spk": w["spk"], "t": w["t0"], "txt": []}
            lines.append(cur)
        cur["txt"].append(w["w"])
        last = w["t1"]
    with open(path, "w") as f:
        f.write(f"# {spec['slug']} — verbatim (mots alignés MMS_FA, marqueurs [euh] et [· silence] calculés sur l'énergie de chaque piste)\n\n")
        for l in lines:
            t = int(l["t"])
            f.write(f"**[{t // 60:02d}:{t % 60:02d}] {l['spk']}** — {' '.join(l['txt'])}\n\n")


slug = spec["slug"]
write_verbatim(os.path.join(D, f"{slug}-verbatim.md"))
if what in ("long", "all", "edl"):
    seg, removed = build(spec["keep"], 0.25)
    m, total = remap(seg)
    raw = sum(r["out"] - r["in"] for r in spec["keep"])
    nh = sum(1 for r in removed if r["why"] == "micro · euh")
    ns = sum(1 for r in removed if r["why"].startswith("micro · silence"))
    print(f"LONG {slug} : {raw / 60:.1f} min retenues -> {total / 60:.1f} min ({len(seg)} segments, {ns} silences réduits, {nh} « euh » retirés)", flush=True)
    edl(seg, removed, os.path.join(WORK, f"edl-{spec.get('long_suffix', 'long')}.json"))
    with open(os.path.join(MONT, f"{slug}-{spec.get('long_suffix', 'long')}-chapitres.txt"), "w") as f:
        for c in spec["chapters"]:
            o = to_out(m, c["t"])
            if o is None:
                o = next((oo for s, e, oo in m if s >= c["t"]), None)
            if o is not None:
                f.write(f"{int(o) // 60:02d}:{int(o) % 60:02d} {c['title']}\n")
    write_srt(captions(seg, 14, 84, 5.0), os.path.join(MONT, f"{slug}-{spec.get('long_suffix', 'long')}.srt"))
    if what != "edl":
        render(seg, "long", os.path.join(MONT, f"{slug}-{spec.get('long_suffix', 'long')}.mp4"))
if what in ("shorts", "all"):
    only = sys.argv[3:] if len(sys.argv) > 3 else None
    for n, sh in enumerate(spec["shorts"], 1):
        name = f"{spec['short_prefix']}{n:02d}-{sh['name']}"
        if only and sh["name"] not in only:
            continue
        seg, removed = build([{"in": sh["in"], "out": sh["out"], "why": f"short · {sh['ligne']}"}], 0.15)
        edl(seg, removed, os.path.join(WORK, f"edl-short-{name}.json"))
        lines = captions(seg, 5, 30, 2.0)
        ass = os.path.join(WORK, f"{name}.ass")
        write_ass(lines, ass)
        write_srt(lines, os.path.join(MONT, f"{name}.srt"), spk=False)
        render(seg, "short", os.path.join(MONT, f"{name}.mp4"), ass=ass)
print("RENDER-FIN", flush=True)
