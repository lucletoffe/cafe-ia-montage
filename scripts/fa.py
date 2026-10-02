#!/usr/bin/env python3
"""Alignement forcé (torchaudio MMS_FA) du texte des segments serveur sur la piste d'un locuteur.
Dépendances : torch + torchaudio (CPU suffit ; voir README).
usage: fa.py <piste.wav> <segments.json> <list|timeline> <Luc|Baptiste> <sortie.json>"""
import json, re, sys, time, unicodedata
import torch, torchaudio
from torchaudio.pipelines import MMS_FA as bundle

wav_path, seg_path, kind, spk, out = sys.argv[1:6]
torch.set_num_threads(16)
HALLU = re.compile(r"sous-titr|radio-canada|amara\.org|ST' ?501|merci d'avoir regardé", re.I)
model = bundle.get_model(with_star=True).eval()
tokenizer, aligner = bundle.get_tokenizer(), bundle.get_aligner()
import wave, numpy as np
with wave.open(wav_path) as wf:  # torchaudio.load passe par torchcodec (CUDA) : lecture directe du PCM 16 bits
    sr, ch = wf.getframerate(), wf.getnchannels()
    a = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0
wav = torch.from_numpy(a.reshape(-1, ch).mean(1)).unsqueeze(0)
if sr != bundle.sample_rate:
    wav = torchaudio.functional.resample(wav, sr, bundle.sample_rate)
SR = bundle.sample_rate
rows = json.load(open(seg_path))
rows = rows["timeline"] if kind == "timeline" else rows
if kind == "timeline":
    rows = [r for r in rows if spk.lower() in r["speaker"].lower()]


def norm(w):
    w = unicodedata.normalize("NFD", w.lower().replace("œ", "oe").replace("æ", "ae").replace("’", "'"))
    w = "".join(c for c in w if not unicodedata.combining(c))
    w = re.sub(r"[^a-z']", "", w).strip("'")
    return w


words, fails, t_start = [], 0, time.time()
for r in rows:
    text = (r.get("text") or "").strip()
    if not text or HALLU.search(text):
        continue
    raw = text.split()
    toks, keep = [], []
    for w in raw:
        n = norm(w)
        if n:
            toks.append(n); keep.append(w)
        elif re.search(r"\d", w):
            toks.append("*"); keep.append(w)
    if not toks:
        continue
    a = max(0.0, float(r["start"]) - 0.25)
    b = float(r["end"]) + 0.35
    seg = wav[:, int(a * SR):int(b * SR)]
    if seg.shape[1] < SR * 0.2:
        continue
    try:
        with torch.inference_mode():
            emission, _ = model(seg)
        spans = aligner(emission[0], tokenizer(toks))
    except Exception:
        fails += 1
        continue
    ratio = seg.shape[1] / emission.shape[1] / SR
    for w, sp in zip(keep, spans):
        words.append({"spk": spk, "w": w, "t0": round(a + sp[0].start * ratio, 3), "t1": round(a + sp[-1].end * ratio, 3),
                      "score": round(sum(s.score * len(s) for s in sp) / max(sum(len(s) for s in sp), 1), 3)})
json.dump(words, open(out, "w"), ensure_ascii=False)
print(f"{spk}: {len(words)} mots alignés, {fails} segments en échec, {time.time() - t_start:.0f} s", flush=True)
