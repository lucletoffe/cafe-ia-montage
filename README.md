# Café IA — montage

Moteur et méthode de montage du Café IA (Luc × Baptiste) : de l'enregistrement brut à une
version longue et à des shorts, en gardant tout l'échange et en ne coupant que les temps morts.

- **`METHODE.md`** — la boucle complète, étape par étape. C'est le fichier à donner à lire à
  son agent (Claude Code ou autre) : il suffit pour refaire un montage de bout en bout.
- **`scripts/`** — le moteur.
- **`examples/`** — les specs réelles des épisodes #1 et #2.

Le code vit ici ; les rushes, les rendus et les docs d'épisode restent dans le dossier
partagé `Cafe-IA/` (Nextcloud). Rien de volumineux dans git.

## Scripts

| Script | Étape | Rôle |
|---|---|---|
| `fa.py` | 3 | Alignement forcé (torchaudio `MMS_FA`) du texte des segments sur la piste d'un locuteur → `work/aligned-<spk>.json`. |
| `render.py` | 3, 5, 6 | Spec éditoriale → EDL (`work/edl-*.json`) → rendus : plages macro de la spec, micro-coupes calées sur l'énergie par piste (silences réduits, silences utiles, « euh »), audio assemblé à l'échantillon avec fondus de 6 ms, vidéo sur la grille de 1/30 s, sous-titres `.srt`/`.ass`, chapitres, verbatim. |
| `calib.py` | 3 | Extraits de calibration des « euh » : fenêtres de 30 s avant / après coupe, à écouter. Les fenêtres sont codées en dur : les adapter. |

```
python3 scripts/render.py examples/spec-002.json [long|shorts|all|edl] [noms de shorts…]
python3 scripts/fa.py <piste.wav> <segments.json> <list|timeline> <Luc|Baptiste> <sortie.json>
CAFE_IA_DIR=~/Files/cafe-ia python3 scripts/calib.py
```

Le champ `dir` de la spec pointe vers le dossier de l'épisode sur ta machine : l'adapter.

## Dépendances

- Python 3.10+, `numpy` ; `ffmpeg` et `ffprobe` dans le PATH.
- `fa.py` seulement : `torch` + `torchaudio` (le CPU suffit).
- Une transcription horodatée par piste de locuteur (Whisper ou équivalent) en entrée.

## Pièges déjà rencontrés

- L'échelle de temps de référence est l'audio enregistré côté serveur de visio. Un Whisper
  avec VAD rend des horodatages sur une timeline compressée (plusieurs minutes d'erreur) :
  ne pas s'en servir pour couper.
- L'expression `select` de ffmpeg est découpée en paquets de 25 termes, sinon ENOMEM
  au-delà d'une centaine de segments.
- Certaines versions de ffmpeg refusent `-filter_complex_script` : passer le graphe par
  fichier avec `-/filter_complex <fichier>`.

## Contribuer

Le dépôt public <https://github.com/lucletoffe/cafe-ia-montage> est un miroir, mis à jour
automatiquement à chaque commit de la forge d'origine. Pour proposer une modification :
**forkez-le sur GitHub, travaillez sur une branche, ouvrez une PR**. Elle est relue puis
intégrée côté forge ; le miroir la rapporte sur GitHub, où elle apparaît alors comme fusionnée.
Ne poussez rien directement sur `main` du miroir : il est réécrit à chaque synchronisation.

Une branche, une PR. Les deux animateurs (et leurs agents) relisent. Une suggestion née
d'une rétro d'épisode (METHODE.md, étape 10) devient une PR ici.
