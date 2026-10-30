# Méthode — monter ce qui s'est passé, lu à travers la ligne

## Le principe

La ligne éditoriale fixe l'intention, l'enregistrement fixe la matière. On ne monte pas ce
qui était prévu : on monte ce qui s'est réellement dit et montré.

- **La version longue garde tout l'échange** : hors-sujet, digressions, humour,
  rapprochements compris — c'est le format café. Seuls partent les temps morts et le
  rythme (« euh », silences longs, faux départs).
- **La ligne choisit** : l'angle, les shorts, les chapitres, les titres. Chaque short cite
  l'élément de ligne qu'il sert. Ce qui ne sert pas la ligne reste dans la version longue
  et au catalogue ; s'il revient souvent, il devient une proposition de modification de la ligne.
- **Chaque passage améliore le suivant** : la rétro (étape 10) alimente la checklist et
  cette méthode elle-même.

## La boucle hebdomadaire

```
S-1  0 Plan ─ sujet + hypothèses d'angles + checklist captation + rétros ouvertes
J    1 Captation (échange normal, enregistré)
J+0  2 Ingest & synchro ─ 3 Transcripts lisible + verbatim ─ 4 Analyse : prévu vs réel → angle + catalogue
J+1  5 Version longue 16:9 ─ 6 Shorts 9:16 ─ 7 QA ─ 8 Livraison
     ── publication = les animateurs, jamais l'agent ──
J+7  9 Stats ─ 10 Rétro → checklist + PR sur ce dépôt + modification de la ligne → étape 0 suivante
N    best-of par catégorie depuis le catalogue des moments
```

Aucune validation humaine entre 2 et 8 : monter coûte peu et se refait. La surface de
revue, ce sont les rendus et le doc d'épisode. La seule barrière est la publication.

**On ne publie que depuis `montages/`.** Un brut (composite, piste d'écran partagé,
piste caméra) ne se publie jamais tel quel, même pour aller vite : il contient tout ce
qui est passé à l'écran, y compris ce que les rendus ont coupé ou flouté.

## Où vivent les choses

| Quoi | Où |
|---|---|
| Ligne éditoriale | `ligne-editoriale-cafe-ia.md`, à la racine du dossier partagé `Cafe-IA/` |
| Dossier d'un épisode | `Cafe-IA/<date>-cafe-ia-<NNN>/` : bruts et transcripts à la racine, intermédiaires dans `work/`, rendus dans `montages/` |
| Plan S-1, angle, catalogue, rétro | dans le dossier de l'épisode : `plan.md`, `work/angle.md`, `work/moments.json`, puis le doc d'épisode |
| Code | ce dépôt |

**Ne jamais purger les bruts d'un épisode dont des moments sont au catalogue** : les
best-of se rendent depuis les sources.

## Étape 0 — Plan S-1 : le sujet de la semaine suivante

Entrées : la ligne ; les rétros ouvertes (étape 10) ; les angles et stats des épisodes
précédents ; les promesses faites à l'antenne (moments `promesse`) ; ce qui a réellement
été construit dans la semaine.

Sortie (`plan.md`) : le sujet en une phrase ; 2 à 4 **hypothèses d'angles** (le moment
qu'on espère capter, l'élément de ligne servi) ; ce qui doit être à l'écran (l'objet, pas
le slide) ; la checklist captation, enrichie des items `[captation]` des rétros ouvertes.
Le plan reste une hypothèse : l'étape 4 le confronte au réel.

## Étape 1 — Captation : c'est là que se décide ce qu'on pourra monter

Leçons : #1 vidéo OBS muette (scène sans source audio) ; #2 vidéo retrouvée après coup
hors du dossier épisode (toujours inventorier les disques de chacun avant de conclure
« pas de vidéo ») ; vignettes de visio trop petites pour un second angle ; aucune caméra
cadrée pour le vertical ; #3 caméra figée et partage d'écran noir.

- [ ] Audio **séparé par voix** (multipiste côté serveur de visio) — vérifier qu'il enregistre.
- [ ] Vidéo **locale de chaque intervenant**, caméra en grand, ≥ 1080p, + capture de l'écran partagé.
- [ ] Test de 10 s relu avant de commencer, en parlant : `volumedetect` → `max_volume` > −30 dB.
- [ ] Un clap au début (mains) : point de synchro pour tous les flux.
- [ ] Cadrage compatible 9:16 : visage centré, marge au-dessus de la tête.
- [ ] Écran partagé propre AVANT de partager : mail, onglets clients, terminaux avec secrets fermés.
- [ ] Pendant l'échange : un client se cite par un nom-code, jamais par son nom ; un passage
      à ne pas publier se signale à l'oral (« ça, on ne le garde pas »).
- [ ] + items `[captation]` des rétros ouvertes.

## Étape 2 — Ingest & synchro → `work/sources.json`

1. Inventorier tous les flux : chemin, type, locuteur, début horloge murale, durée,
   résolution, fps, `audio_ok`.
2. Détecter les pistes muettes (`volumedetect`) — ne jamais monter sans.
3. Synchroniser : décalage initial par horloge murale, **affiné par corrélation croisée**
   des enveloppes audio (ou par le clap) — l'horloge murale seule se trompe de quelques
   centaines de ms. Noter l'offset de chaque flux.
4. Flux incomplet → mode dégradé, le dire dans le doc d'épisode.
5. **Planche de l'écran partagé**, pour chaque piste d'écran : une image toutes les 5 s et
   à chaque changement d'écran, regardées **toutes** (2 min de partage ≈ 25 images). Tout
   passage qui montre une interface d'administration, une liste de personnes, une adresse
   e-mail, un lien ou un jeton d'accès, un document client → plage `ecran-sensible`
   dans `work/sources.json`, coupée ou floutée dans **tous** les rendus. Un lien ou un
   jeton d'accès vu à l'écran se signale tout de suite aux animateurs : il se régénère,
   même si les rendus le floutent, puisque le brut le garde. Une détection automatique
   (OCR) peut aider à repérer, jamais remplacer la planche.

## Étape 3 — Deux transcripts : lisible et verbatim

**Pourquoi deux** : mesuré sur 90 s denses, Whisper large-v3 rend 0 hésitation sur 290
mots, avec ou sans amorce dans le prompt. Le texte de Whisper ne dira jamais où sont les « euh ».

1. **Lisible** → `work/words.json` + transcript `.md` : une transcription par piste de
   locuteur, horodatée au mot. Sert à LIRE et à choisir les moments. Retirer les
   hallucinations sur silence (« Sous-titrage Société Radio-Canada », « Merci d'avoir regardé »…).
   Piège : un Whisper avec VAD rend des horodatages sur une timeline compressée — ne pas
   les utiliser pour couper.
2. **Verbatim** → `work/verbatim.json` + verbatim `.md` : sert à décider QUOI COUPER.
   - **Alignement forcé** du texte lisible sur l'audio de chaque piste (`scripts/fa.py`,
     ±20–30 ms) : frontières de mots précises.
   - **Énergie vocale non couverte par un mot aligné** sur la piste du locuteur →
     `[euh 0,4 s]` ; silence de toutes les pistes → `[· 1,2 s]` ; énergie sur la piste de
     l'autre pendant que le locuteur parle → `[chevauchement]` ; rafale sans mots juste
     après un moment → `[rire ?]`.
   - Chaque marqueur porte ses horodatages et devient une proposition de coupe micro (étape 5).
   - L'énergie seule produit des faux `[euh]` (respiration, clavier, ventilateur) : seuils
     par piste, calés sur le bruit de fond mesuré dans ses silences.
   - Premier passage : 3 extraits de 30 s à écouter avec leurs marqueurs
     (`scripts/calib.py`) avant de faire confiance aux seuils.

## Étape 4 — Analyse éditoriale : prévu vs réel, angle, catalogue

Lire le transcript lisible **en entier**, ligne et plan S-1 ouverts.

**Catalogue des moments** → `work/moments.json`. Catégories (plusieurs par moment) :

| Catégorie | C'est quoi |
|---|---|
| `bourde` | raté technique, erreur, lapsus, truc qui plante en direct |
| `punchline` | phrase forte, citable seule |
| `fou-rire` | rire franc, d'un ou des deux |
| `rapprochement` | analogie, lien inattendu entre deux mondes |
| `aveu` | ce qui n'a pas marché, doute, coût réel avoué |
| `objet-visible` | le construit qui apparaît à l'écran |
| `digression` | hors-sujet savoureux |
| `desaccord` | friction amicale, deux avis |
| `methode` | façon de faire transmissible |
| `chiffre` | ordre de grandeur, coût, durée |
| `promesse` | engagement pour la suite — sert l'étape 0, pas les best-of |

Champs : `start`, `end` (secondes, timeline de la piste de référence), `speaker`,
`verbatim`, `categories`, `intensite` 1–5, `autonome` (compréhensible sans contexte ?),
`publiable` (`oui` · `accord` · `non`), `ligne` (critère servi, ou vide), `raison`.

Règles de `publiable` : client ou tiers nommé à l'oral → `non` tant que le nom n'est pas
coupé ou bipé ; passage signalé « on ne le garde pas » → `non` ; autodérision et bourdes
publiables sur l'outil et le bricolage logiciel, **jamais sur le métier vendu** → `non` ;
écran sensible à l'image → `non` tant qu'il n'est pas flouté.

**`work/angle.md`** (base du doc d'épisode) :
1. **Prévu vs réel** : chaque hypothèse du plan → captée / pas captée / remplacée par quoi.
2. **Angle retenu** : une phrase, l'élément de ligne servi, les 3 à 5 moments qui le portent.
3. **Hors ligne** : ce qui a de la valeur sans entrer dans la ligne.
4. **Fils pour S+1** : moments `promesse`, questions restées ouvertes.

## Étape 5 — Version longue 16:9 → `work/edl-long.json`, `montages/<épisode>-long.mp4`

On ne coupe jamais « à la main » dans une commande ffmpeg : toute coupe passe par l'EDL,
reproductible et relisible (`scripts/render.py`, une spec par épisode, voir `examples/`).

**Niveau macro : on garde tout l'échange.** Ne partent que les temps morts : attente avant
que l'autre arrive, « tu m'entends ? », installation silencieuse, fin après « on coupe ».
Chaque retrait est journalisé avec sa raison. Chronologie conservée, à une exception près :
un cold open ≤ 15 s du meilleur moment, suivi d'un carton qui marque le vrai début.

**Niveau micro (rythme)**, coupes calées sur les frontières alignées et l'énergie audio,
jamais au milieu d'un mot :
- `[euh]` → coupé, 40 ms de marge ;
- faux départ / phrase reprise → on garde la dernière version ;
- silence > 0,6 s → **réduit** à 0,25 s, pas supprimé.

**Silences utiles — testés d'abord, jamais réduits à 0,25 s :**
- suivis d'un rire ou d'une réaction sur la piste de l'autre ;
- l'écran bouge pendant le silence (démo en cours) ;
- pause après une question ou une punchline (plafond 1,2 s) ;
- temps de réflexion avant un aveu (plafond 1,5 s).

**Garde-fous anti-hachage** : segment conservé ≥ 1 s ; fondu audio à chaque coupe ; en cas
de doute, on garde.

**Plans** : qui parle → sa caméra (plan ≥ 2 s) ; écran partagé en grand quand il change,
vignette du locuteur. **Rendu** : loudnorm I=−14 LUFS, TP=−1 ; chapitres ; `.srt` à côté.

## Étape 6 — Shorts 9:16 → `work/edl-short-NN.json`, `montages/NN-<slug>.mp4`

- 3 à 6 shorts. Un short = une idée = un moment (ou deux contigus) d'intensité ≥ 4,
  `autonome`, `publiable` ≠ `non`, qui cite son élément de ligne.
- Au moins un short par mois porte un **signal de compétence** (`methode` ou `chiffre`).
- Structure : l'accroche dans les 2 premières secondes → le développement → la fin sur la
  réaction de l'autre si elle existe.
- 20 à 60 s ; micro-coupes plus serrées (silence → 0,15 s), mêmes silences utiles.
- Recadrage 9:16 sur le locuteur actif ; démo = écran en haut, visage en bas. **Vérifier
  le cadrage sur des images extraites à chaque coupe.**
- Sous-titres incrustés par groupes de 3 à 5 mots, hors du bas 20 % et de la colonne
  d'icônes à droite.
- Un fichier et un texte de post **par publieur** : chacun poste le fichier natif.

## Étape 7 — QA automatique, avant de montrer quoi que ce soit

Pour chaque rendu : `ffprobe` (durée, pistes) ; audio non muet ; `ebur128` à ±1 LU de la
cible ; `blackdetect` vide ; images extraites à chaque coupe et **regardées** (cadrage,
visage entier, sous-titres en zone sûre) ; pour chaque plage `ecran-sensible` gardée dans
le rendu, une image toutes les 5 s **à l'intérieur** de la plage, regardée : rien n'y est
lisible ; re-transcription du rendu pour vérifier qu'aucune phrase n'est tronquée. Un échec corrige l'EDL et relance le rendu.
On ne livre jamais un rendu en échec.

## Étape 8 — Livraison

**Doc d'épisode** `<épisode>-episode.md`, dans le dossier de l'épisode à côté de
`montages/` : prévu vs réel ; angle retenu ; tableau des shorts (fichier, durée, accroche,
élément de ligne, texte de post de chacun, **colonne vide « lien publié »** que chaque
publieur remplit) ; chapitres ; moments catalogués par catégorie ; consentements à
recueillir (moments `publiable = accord`) ; rétro ; sujet proposé pour S+1.

Validation des extraits par chaque personne qui y apparaît : délai fixé par la ligne ;
sans réponse dans le délai, seuls les moments `publiable = oui` sont publiables.

## Étape 9 — Stats par short (J+3 / J+7)

Sans le lien publié, aucune stat : il se lit dans la colonne du doc d'épisode.
- Compteurs publics (réactions, commentaires, republications) : lisibles par tous.
- Impressions, vues, temps de visionnage : visibles **par l'auteur seul** — chacun dépose
  son export de statistiques dans le dossier de l'épisode.
- Sortie : tableau par short dans le doc d'épisode + lecture « quels éléments de ligne,
  quelles catégories portent ».
- Les métriques de pilotage et la règle d'arrêt sont celles de la ligne : les reporter
  telles quelles, rouge compris.

## Étape 10 — Rétro : ce qui doit changer la prochaine fois

À la fin de chaque passage, lister les suggestions, chacune taguée :
- `[captation]` → ajoutée à la checklist de l'étape 1 du plan suivant ;
- `[montage]` / `[methode]` → **PR sur ce dépôt** ;
- `[ligne]` → proposition de modification de la ligne, à valider par les deux animateurs.

La rétro figure dans le doc d'épisode, pour que chacun puisse en ajouter.

## Mode best-of

Moments `publiable = oui` d'une catégorie, tous épisodes confondus, triés par intensité ;
EDL de compilation depuis les bruts, carton titre par moment (épisode + date), mêmes règles
de rythme et de QA que les shorts ; livrable horizontal et vertical.

## Modes dégradés

- **Audio seul** : version longue = audio avec les mêmes coupes ; pas de short vidéo —
  citations écrites pour les posts. Les moments vont quand même au catalogue.
- **Un seul flux vidéo** : pas d'alternance de plans ; 9:16 recadré sur ce flux.
- **Pas de piste séparée par voix** : diarisation ; marqueurs `[rire ?]` et
  `[chevauchement]` désactivés (non fiables sur un mix).
